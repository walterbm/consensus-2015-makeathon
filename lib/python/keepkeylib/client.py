import os
import sys
import time
import binascii
import hashlib
import unicodedata
import mapping
import json
import getpass
import getch

import tools
import messages_pb2 as proto
import types_pb2 as types
import protobuf_json
from keepkeylib.debuglink import DebugLink
from mnemonic import Mnemonic


# try:
#     from PIL import Image
#     SCREENSHOT = True
# except:
#     SCREENSHOT = False

SCREENSHOT = False

DEFAULT_CURVE = 'secp256k1'

# monkeypatching: text formatting of protobuf messages
tools.monkeypatch_google_protobuf_text_format()

def get_buttonrequest_value(code):
    # Converts integer code to its string representation of ButtonRequestType
    return [ k for k, v in types.ButtonRequestType.items() if v == code][0]

def pprint(msg):
    msg_class = msg.__class__.__name__
    msg_size = msg.ByteSize()
    """
    msg_ser = msg.SerializeToString()
    msg_id = mapping.get_type(msg)
    msg_json = json.dumps(protobuf_json.pb2json(msg))
    """
    if isinstance(msg, proto.FirmwareUpload):
        return "<%s> (%d bytes):\n" % (msg_class, msg_size)
    else:
        return "<%s> (%d bytes):\n%s" % (msg_class, msg_size, msg)

def log(msg):
    sys.stderr.write("%s\n" % msg)
    sys.stderr.flush()

def log_cr(msg):
    sys.stdout.write('\r%s' % msg)
    sys.stdout.flush()

def log_backspace(times):
    for _ in range(times):
        sys.stdout.write('\b')
        sys.stdout.flush()

def format_mnemonic(word_pos, character_pos):
    return "WORD %d: %s" % (word_pos, character_pos * '*')

class CallException(Exception):
    def __init__(self, code, message):
        super(CallException, self).__init__()
        self.args = [code, message]

class PinException(CallException):
    pass

class field(object):
    # Decorator extracts single value from
    # protobuf object. If the field is not
    # present, raises an exception.
    def __init__(self, field):
        self.field = field

    def __call__(self, f):
        def wrapped_f(*args, **kwargs):
            ret = f(*args, **kwargs)
            ret.HasField(self.field)
            return getattr(ret, self.field)
        return wrapped_f

class expect(object):
    # Decorator checks if the method
    # returned one of expected protobuf messages
    # or raises an exception
    def __init__(self, *expected):
        self.expected = expected
        
    def __call__(self, f):
        def wrapped_f(*args, **kwargs):
            ret = f(*args, **kwargs)
            if not isinstance(ret, self.expected):
                raise Exception("Got %s, expected %s" % (ret.__class__, self.expected))
            return ret
        return wrapped_f

def normalize_nfc(txt):
    # Normalize string to UTF8 NFC for sign_message
    if isinstance(txt, str):
        utxt = txt.decode('utf8')
    elif isinstance(txt, unicode):
        utxt = txt
    else:
        raise Exception("String value expected")

    return unicodedata.normalize('NFC', utxt)

class BaseClient(object):
    # Implements very basic layer of sending raw protobuf
    # messages to device and getting its response back.
    def __init__(self, transport, **kwargs):
        self.transport = transport
        super(BaseClient, self).__init__()  # *args, **kwargs)

    def cancel(self):
        self.transport.write(proto.Cancel())

    def call_raw(self, msg):
        try:
            self.transport.session_begin()
            self.transport.write(msg)
            resp = self.transport.read_blocking()
        finally:
            self.transport.session_end()

        return resp

    def call(self, msg):
        try:
            self.transport.session_begin()

            resp = self.call_raw(msg)
            handler_name = "callback_%s" % resp.__class__.__name__
            handler = getattr(self, handler_name, None)

            if handler != None:
                msg = handler(resp)
                if msg == None:
                    raise Exception("Callback %s must return protobuf message, not None" % handler)

                resp = self.call(msg)

        finally:
            self.transport.session_end()

        return resp

    def callback_Failure(self, msg):
        if msg.code in (types.Failure_PinInvalid,
            types.Failure_PinCancelled, types.Failure_PinExpected):
            raise PinException(msg.code, msg.message)

        raise CallException(msg.code, msg.message)

    def close(self):
        self.transport.close()

class DebugWireMixin(object):
    def call_raw(self, msg):
        log("SENDING " + pprint(msg))
        resp = super(DebugWireMixin, self).call_raw(msg)
        log("RECEIVED " + pprint(resp))
        return resp

class TextUIMixin(object):
    # This class demonstrates easy test-based UI
    # integration between the device and wallet.
    # You can implement similar functionality
    # by implementing your own GuiMixin with
    # graphical widgets for every type of these callbacks.

    def __init__(self, *args, **kwargs):
        super(TextUIMixin, self).__init__(*args, **kwargs)

        self.character_request_first_pass = True

    def callback_ButtonRequest(self, msg):
        # log("Sending ButtonAck for %s " % get_buttonrequest_value(msg.code))
        return proto.ButtonAck()

    def callback_PinMatrixRequest(self, msg):
        if msg.type == 1:
            desc = 'current PIN'
        elif msg.type == 2:
            desc = 'new PIN'
        elif msg.type == 3:
            desc = 'new PIN again'
        else:
            desc = 'PIN'

        log("Please enter %s: " % desc)
        pin = getpass.getpass('')
        return proto.PinMatrixAck(pin=pin)

    def callback_PassphraseRequest(self, msg):
        log("Passphrase required: ")
        passphrase = getpass.getpass('')
        log("Confirm your Passphrase: ")
        if passphrase == getpass.getpass(''):
            passphrase = unicode(str(bytearray(passphrase, 'utf-8')), 'utf-8')
            return proto.PassphraseAck(passphrase=passphrase)
        else:
            log("Passphrase did not match! ")
            exit()

    def callback_WordRequest(self, msg):
        log("Enter one word of mnemonic: ")
        word = raw_input()
        return proto.WordAck(word=word)

    def callback_CharacterRequest(self, msg):
        if self.character_request_first_pass:
            self.character_request_first_pass = False
            log("Use recovery cipher on device to input mnemonic. Words are autocompleted at 3 or 4 characters.")
            log("(use spacebar to progress to next word after match, use backspace to correct bad character or word entries)")

        # format mnemonic for console
        formatted_console = format_mnemonic(msg.word_pos + 1, msg.character_pos)

        # clear the runway before we display formatted mnemonic
        log_cr(' ' * 14)
        log_cr(formatted_console)

        while True:
            character = getch.getch().lower()
            character_ascii = ord(character)

            if character_ascii >= 97 and character_ascii <= 122 \
            and msg.character_pos != 4:
                # capture characters a-z
                return proto.CharacterAck(character=character)

            elif character_ascii == 32 and msg.word_pos < 23 \
            and msg.character_pos >= 3:
                # capture spaces
                return proto.CharacterAck(character=' ')

            elif character_ascii == 127 \
            and (msg.word_pos > 0 or msg.character_pos > 0):
                # capture backspaces
                return proto.CharacterAck(delete=True)

            elif character_ascii == 10 and msg.word_pos in (11, 17, 23):
                # capture returns
                log("")
                return proto.CharacterAck(done=True)

class DebugLinkMixin(object):
    # This class implements automatic responses
    # and other functionality for unit tests
    # for various callbacks, created in order
    # to automatically pass unit tests.
    #
    # This mixing should be used only for purposes
    # of unit testing, because it will fail to work
    # without special DebugLink interface provided
    # by the device.

    def __init__(self, *args, **kwargs):
        super(DebugLinkMixin, self).__init__(*args, **kwargs)
        self.debug = None
        self.in_with_statement = 0
        self.button_wait = 0
        self.screenshot_id = 0

        # Always press Yes and provide correct pin
        self.setup_debuglink(True, True)
        
        # Do not expect any specific response from device
        self.expected_responses = None

        # Use blank passphrase
        self.set_passphrase('')

    def close(self):
        super(DebugLinkMixin, self).close()
        if self.debug:
            self.debug.close()

    def set_debuglink(self, debug_transport):
        self.debug = DebugLink(debug_transport)

    def set_buttonwait(self, secs):
        self.button_wait = secs

    def __enter__(self):
        # For usage in with/expected_responses
        self.in_with_statement += 1
        return self

    def __exit__(self, _type, value, traceback):
        self.in_with_statement -= 1

        if _type != None:
            # Another exception raised
            return False

        # return isinstance(value, TypeError)
        # Evaluate missed responses in 'with' statement
        if self.expected_responses != None and len(self.expected_responses):
            raise Exception("Some of expected responses didn't come from device: %s" % \
                    [ pprint(x) for x in self.expected_responses ])

        # Cleanup
        self.expected_responses = None
        return False

    def set_expected_responses(self, expected):
        if not self.in_with_statement:
            raise Exception("Must be called inside 'with' statement")
        self.expected_responses = expected

    def setup_debuglink(self, button, pin_correct):
        self.button = button  # True -> YES button, False -> NO button
        self.pin_correct = pin_correct

    def set_passphrase(self, passphrase):
        self.passphrase = unicode(str(bytearray(Mnemonic.normalize_string(passphrase), 'utf-8')), 'utf-8')

    def set_mnemonic(self, mnemonic):
        self.mnemonic = unicode(str(bytearray(Mnemonic.normalize_string(mnemonic), 'utf-8')), 'utf-8').split(' ')

    def call_raw(self, msg):

        if SCREENSHOT and self.debug:
            layout = self.debug.read_layout()
            im = Image.new("RGB", (128, 64))
            pix = im.load()
            for x in range(128):
                for y in range(64):
                    rx, ry = 127 - x, 63 - y
                    if (ord(layout[rx + (ry / 8) * 128]) & (1 << (ry % 8))) > 0:
                        pix[x, y] = (255, 255, 255)
            im.save('scr%05d.png' % self.screenshot_id)
            self.screenshot_id += 1

        resp = super(DebugLinkMixin, self).call_raw(msg)
        self._check_request(resp)
        return resp
        
    def _check_request(self, msg):
        if self.expected_responses != None:
            try:
                expected = self.expected_responses.pop(0)
            except IndexError:
                raise CallException(types.Failure_Other,
                        "Got %s, but no message has been expected" % pprint(msg))

            if msg.__class__ != expected.__class__:
                raise CallException(types.Failure_Other,
                            "Expected %s, got %s" % (pprint(expected), pprint(msg)))

            fields = expected.ListFields()  # only filled (including extensions)
            for field, value in fields:
                if not msg.HasField(field.name) or getattr(msg, field.name) != value:
                    raise CallException(types.Failure_Other,
                            "Expected %s, got %s" % (pprint(expected), pprint(msg)))
            
    def callback_ButtonRequest(self, msg):
        log("ButtonRequest code: " + get_buttonrequest_value(msg.code))

        log("Pressing button " + str(self.button))
        if self.button_wait:
            log("Waiting %d seconds " % self.button_wait)
            time.sleep(self.button_wait)
        self.debug.press_button(self.button)
        return proto.ButtonAck()

    def callback_PinMatrixRequest(self, msg):
        if self.pin_correct:
            pin = self.debug.read_pin_encoded()
        else:
            pin = '444222'
        return proto.PinMatrixAck(pin=pin)

    def callback_PassphraseRequest(self, msg):
        log("Provided passphrase: '%s'" % self.passphrase)
        return proto.PassphraseAck(passphrase=self.passphrase)

    def callback_WordRequest(self, msg):
        (word, pos) = self.debug.read_recovery_word()
        if word != '':
            return proto.WordAck(word=word)
        if pos != 0:
            return proto.WordAck(word=self.mnemonic[pos - 1])

        raise Exception("Unexpected call")

class ProtocolMixin(object):
    PRIME_DERIVATION_FLAG = 0x80000000
    VENDORS = ('keepkey.com',)

    def __init__(self, *args, **kwargs):
        super(ProtocolMixin, self).__init__(*args, **kwargs)
        self.init_device()
        self.tx_api = None

    def set_tx_api(self, tx_api):
        self.tx_api = tx_api

    def init_device(self):
        self.features = expect(proto.Features)(self.call)(proto.Initialize())
        if str(self.features.vendor) not in self.VENDORS:
            raise Exception("Unsupported device")

    def _get_local_entropy(self):
        return os.urandom(32)

    def _convert_prime(self, n):
        # Convert minus signs to uint32 with flag
        return [ int(abs(x) | self.PRIME_DERIVATION_FLAG) if x < 0 else x for x in n ]

    def expand_path(self, n):
        # Convert string of bip32 path to list of uint32 integers with prime flags
        # 0/-1/1' -> [0, 0x80000001, 0x80000001]
        if not n:
            return []

        n = n.split('/')
        path = []
        for x in n:
            prime = False
            if x.endswith("'"):
                x = x.replace('\'', '')
                prime = True
            if x.startswith('-'):
                prime = True

            x = abs(int(x))

            if prime:
                x |= self.PRIME_DERIVATION_FLAG

            path.append(x)

        return path

    @expect(proto.PublicKey)
    def get_public_node(self, n, ecdsa_curve_name=DEFAULT_CURVE):
        n = self._convert_prime(n)
        return self.call(proto.GetPublicKey(address_n=n))

    @field('address')
    @expect(proto.Address)
    def get_address(self, coin_name, n, show_display=False, multisig=None):
        n = self._convert_prime(n)
        if multisig:
            return self.call(proto.GetAddress(address_n=n, coin_name=coin_name, show_display=show_display, multisig=multisig))
        else:
            return self.call(proto.GetAddress(address_n=n, coin_name=coin_name, show_display=show_display))

    @field('entropy')
    @expect(proto.Entropy)
    def get_entropy(self, size):
        return self.call(proto.GetEntropy(size=size))

    @field('message')
    @expect(proto.Success)
    def ping(self, msg, button_protection=False, pin_protection=False, passphrase_protection=False):
        msg = proto.Ping(message=msg,
                         button_protection=button_protection,
                         pin_protection=pin_protection,
                         passphrase_protection=passphrase_protection)
        return self.call(msg)

    def get_device_id(self):
        return self.features.device_id

    @field('message')
    @expect(proto.Success)
    def apply_settings(self, label=None, language=None, use_passphrase=None):
        settings = proto.ApplySettings()
        if label != None:
            settings.label = label
        if language:
            settings.language = language
        if use_passphrase != None:
            settings.use_passphrase = use_passphrase

        out = self.call(settings)
        self.init_device()  # Reload Features
        return out

    @field('message')
    @expect(proto.Success)
    def clear_session(self):
        return self.call(proto.ClearSession())

    @field('message')
    @expect(proto.Success)
    def change_pin(self, remove=False):
        ret = self.call(proto.ChangePin(remove=remove))
        self.init_device()  # Re-read features
        return ret

    @expect(proto.MessageSignature)
    def sign_message(self, coin_name, n, message):
        n = self._convert_prime(n)

        try:
            # Convert message to UTF8 NFC (seems to be a bitcoin-qt standard)
            message = normalize_nfc(message)
            # Convert message to ASCII stream
            message = str(bytearray(message, 'utf-8'))
        except:
            pass # it was not UTF8 string

        return self.call(proto.SignMessage(coin_name=coin_name, address_n=n, message=message))

    @expect(proto.SignedIdentity)
    def sign_identity(self, identity, challenge_hidden, challenge_visual, ecdsa_curve_name=DEFAULT_CURVE):
        return self.call(proto.SignIdentity(identity=identity, challenge_hidden=challenge_hidden, challenge_visual=challenge_visual))

    def verify_message(self, address, signature, message):
        try:
            # Convert message to UTF8 NFC (seems to be a bitcoin-qt standard)
            message = normalize_nfc(message)
        # Convert message to ASCII stream
            message = str(bytearray(message, 'utf-8'))
        except:
            pass # it was not UTF8 string

        try:
            if address:
                resp = self.call(proto.VerifyMessage(address=address, signature=signature, message=message))
            else:
                resp = self.call(proto.VerifyMessage(signature=signature, message=message))
        except CallException as e:
            resp = e
        if isinstance(resp, proto.Success):
            return True
        return False

    @expect(proto.EncryptedMessage)
    def encrypt_message(self, pubkey, message, display_only, coin_name, n):
        if coin_name and n:
            n = self._convert_prime(n)
            return self.call(proto.EncryptMessage(pubkey=pubkey, message=message, display_only=display_only, coin_name=coin_name, address_n=n))
        else:
            return self.call(proto.EncryptMessage(pubkey=pubkey, message=message, display_only=display_only))

    @expect(proto.DecryptedMessage)
    def decrypt_message(self, n, nonce, message, msg_hmac):
        n = self._convert_prime(n)
        return self.call(proto.DecryptMessage(address_n=n, nonce=nonce, message=message, hmac=msg_hmac))

    @field('value')
    @expect(proto.CipheredKeyValue)
    def encrypt_keyvalue(self, n, key, value, ask_on_encrypt=True, ask_on_decrypt=True):
        n = self._convert_prime(n)
        return self.call(proto.CipherKeyValue(address_n=n,
                                              key=key,
                                              value=value,
                                              encrypt=True,
                                              ask_on_encrypt=ask_on_encrypt,
                                              ask_on_decrypt=ask_on_decrypt))

    @field('value')
    @expect(proto.CipheredKeyValue)
    def decrypt_keyvalue(self, n, key, value, ask_on_encrypt=True, ask_on_decrypt=True):
        n = self._convert_prime(n)
        return self.call(proto.CipherKeyValue(address_n=n,
                                              key=key,
                                              value=value,
                                              encrypt=False,
                                              ask_on_encrypt=ask_on_encrypt,
                                              ask_on_decrypt=ask_on_decrypt))

    @field('tx_size')
    @expect(proto.TxSize)
    def estimate_tx_size(self, coin_name, inputs, outputs):
        msg = proto.EstimateTxSize()
        msg.coin_name = coin_name
        msg.inputs_count = len(inputs)
        msg.outputs_count = len(outputs)
        return self.call(msg)

    def _prepare_simple_sign_tx(self, coin_name, inputs, outputs):
        msg = proto.SimpleSignTx()
        msg.coin_name = coin_name
        msg.inputs.extend(inputs)
        msg.outputs.extend(outputs)

        known_hashes = []
        for inp in inputs:
            if inp.prev_hash in known_hashes:
                continue

            tx = msg.transactions.add()
            if self.tx_api:
                tx.CopyFrom(self.tx_api.get_tx(binascii.hexlify(inp.prev_hash)))
            else:
                raise Exception('TX_API not defined')
            known_hashes.append(inp.prev_hash)

        return msg

    def simple_sign_tx(self, coin_name, inputs, outputs):
        msg = self._prepare_simple_sign_tx(coin_name, inputs, outputs)
        return self.call(msg).serialized.serialized_tx

    def _prepare_sign_tx(self, coin_name, inputs, outputs):
        tx = types.TransactionType()
        tx.inputs.extend(inputs)
        tx.outputs.extend(outputs)

        txes = {}
        txes[''] = tx

        known_hashes = []
        for inp in inputs:
            if inp.prev_hash in known_hashes:
                continue

            if self.tx_api:
                txes[inp.prev_hash] = self.tx_api.get_tx(binascii.hexlify(inp.prev_hash))
            else:
                raise Exception('TX_API not defined')
            known_hashes.append(inp.prev_hash)

        return txes

    def sign_tx(self, coin_name, inputs, outputs, debug_processor=None):

        start = time.time()
        txes = self._prepare_sign_tx(coin_name, inputs, outputs)

        try:
            self.transport.session_begin()

            # Prepare and send initial message
            tx = proto.SignTx()
            tx.inputs_count = len(inputs)
            tx.outputs_count = len(outputs)
            tx.coin_name = coin_name
            res = self.call(tx)

            # Prepare structure for signatures
            signatures = [None] * len(inputs)
            serialized_tx = ''

            counter = 0
            while True:
                counter += 1

                if isinstance(res, proto.Failure):
                    raise CallException("Signing failed")

                if not isinstance(res, proto.TxRequest):
                    raise CallException("Unexpected message")

                # If there's some part of signed transaction, let's add it
                if res.HasField('serialized') and res.serialized.HasField('serialized_tx'):
                    log("RECEIVED PART OF SERIALIZED TX (%d BYTES)" % len(res.serialized.serialized_tx))
                    serialized_tx += res.serialized.serialized_tx

                if res.HasField('serialized') and res.serialized.HasField('signature_index'):
                    if signatures[res.serialized.signature_index] != None:
                        raise Exception("Signature for index %d already filled" % res.serialized.signature_index)
                    signatures[res.serialized.signature_index] = res.serialized.signature

                if res.request_type == types.TXFINISHED:
                    # Device didn't ask for more information, finish workflow
                    break

                # Device asked for one more information, let's process it.
                current_tx = txes[res.details.tx_hash]

                if res.request_type == types.TXMETA:
                    msg = types.TransactionType()
                    msg.version = current_tx.version
                    msg.lock_time = current_tx.lock_time
                    msg.inputs_cnt = len(current_tx.inputs)
                    if res.details.tx_hash:
                        msg.outputs_cnt = len(current_tx.bin_outputs)
                    else:
                        msg.outputs_cnt = len(current_tx.outputs)
                    res = self.call(proto.TxAck(tx=msg))
                    continue

                elif res.request_type == types.TXINPUT:
                    msg = types.TransactionType()
                    msg.inputs.extend([current_tx.inputs[res.details.request_index], ])
                    res = self.call(proto.TxAck(tx=msg))
                    continue

                elif res.request_type == types.TXOUTPUT:
                    msg = types.TransactionType()
                    if res.details.tx_hash:
                        msg.bin_outputs.extend([current_tx.bin_outputs[res.details.request_index], ])
                    else:
                        msg.outputs.extend([current_tx.outputs[res.details.request_index], ])

                    if debug_processor != None:
                        # If debug_processor function is provided,
                        # pass thru it the request and prepared response.
                        # This is useful for unit tests, see test_msg_signtx
                        msg = debug_processor(res, msg)

                    res = self.call(proto.TxAck(tx=msg))
                    continue

        finally:
            self.transport.session_end()

        if None in signatures:
            raise Exception("Some signatures are missing!")

        log("SIGNED IN %.03f SECONDS, CALLED %d MESSAGES, %d BYTES" % \
                (time.time() - start, counter, len(serialized_tx)))

        return (signatures, serialized_tx)

    @field('message')
    @expect(proto.Success)
    def wipe_device(self):
        ret = self.call(proto.WipeDevice())
        self.init_device()
        return ret

    @field('message')
    @expect(proto.Success)
    def recovery_device(self, use_trezor_method, word_count, passphrase_protection, pin_protection, label, language):
        if self.features.initialized:
            raise Exception("Device is initialized already. Call wipe_device() and try again.")

        if not use_trezor_method:
            word_count = 0
        elif word_count not in (12, 18, 24):
            raise Exception("Invalid word count. Use 12/18/24")

        res = self.call(proto.RecoveryDevice(word_count=int(word_count),
                                    passphrase_protection=bool(passphrase_protection),
                                    pin_protection=bool(pin_protection),
                                    label=label,
                                    language=language,
                                    enforce_wordlist=True,
                                    use_character_cipher=bool(not use_trezor_method)))

        self.init_device()
        return res

    @field('message')
    @expect(proto.Success)
    def reset_device(self, display_random, strength, passphrase_protection, pin_protection, label, language):
        if self.features.initialized:
            raise Exception("Device is initialized already. Call wipe_device() and try again.")

        # Begin with device reset workflow
        msg = proto.ResetDevice(display_random=display_random,
                                strength=strength,
                                language=language,
                                passphrase_protection=bool(passphrase_protection),
                                pin_protection=bool(pin_protection),
                                label=label)

        resp = self.call(msg)
        if not isinstance(resp, proto.EntropyRequest):
            raise Exception("Invalid response, expected EntropyRequest")

        external_entropy = self._get_local_entropy()
        log("Computer generated entropy: " + binascii.hexlify(external_entropy))
        ret = self.call(proto.EntropyAck(entropy=external_entropy))
        self.init_device()
        return ret

    @field('message')
    @expect(proto.Success)
    def load_device_by_mnemonic(self, mnemonic, pin, passphrase_protection, label, language, skip_checksum=False):
        m = Mnemonic('english')
        if not skip_checksum and not m.check(mnemonic):
            raise Exception("Invalid mnemonic checksum")

        # Convert mnemonic to UTF8 NKFD
        mnemonic = Mnemonic.normalize_string(mnemonic)

        # Convert mnemonic to ASCII stream
        mnemonic = unicode(str(bytearray(mnemonic, 'utf-8')), 'utf-8')

        if self.features.initialized:
            raise Exception("Device is initialized already. Call wipe_device() and try again.")

        resp = self.call(proto.LoadDevice(mnemonic=mnemonic, pin=pin,
                                          passphrase_protection=passphrase_protection,
                                          language=language,
                                          label=label,
                                          skip_checksum=skip_checksum))
        self.init_device()
        return resp

    @field('message')
    @expect(proto.Success)
    def load_device_by_xprv(self, xprv, pin, passphrase_protection, label, language):
        if self.features.initialized:
            raise Exception("Device is initialized already. Call wipe_device() and try again.")

        if xprv[0:4] not in ('xprv', 'tprv'):
            raise Exception("Unknown type of xprv")

        if len(xprv) < 100 and len(xprv) > 112:
            raise Exception("Invalid length of xprv")

        node = types.HDNodeType()
        data = tools.b58decode(xprv, None).encode('hex')

        if data[90:92] != '00':
            raise Exception("Contain invalid private key")

        checksum = hashlib.sha256(hashlib.sha256(binascii.unhexlify(data[:156])).digest()).hexdigest()[:8]
        if checksum != data[156:]:
            raise Exception("Checksum doesn't match")

        # version 0488ade4
        # depth 00
        # fingerprint 00000000
        # child_num 00000000
        # chaincode 873dff81c02f525623fd1fe5167eac3a55a049de3d314bb42ee227ffed37d508
        # privkey   00e8f32e723decf4051aefac8e2c93c9c5b214313817cdb01a1494b917c8436b35
        # checksum e77e9d71

        node.depth = int(data[8:10], 16)
        node.fingerprint = int(data[10:18], 16)
        node.child_num = int(data[18:26], 16)
        node.chain_code = data[26:90].decode('hex')
        node.private_key = data[92:156].decode('hex')  # skip 0x00 indicating privkey

        resp = self.call(proto.LoadDevice(node=node,
                                          pin=pin,
                                          passphrase_protection=passphrase_protection,
                                          language=language,
                                          label=label))
        self.init_device()
        return resp

    def firmware_update(self, fp):
        if self.features.bootloader_mode == False:
            raise Exception("Device must be in bootloader mode")

        resp = self.call(proto.FirmwareErase())
        if isinstance(resp, proto.Failure) and resp.code == types.Failure_FirmwareError:
            return False

        data = fp.read()
        data_hash = hashlib.sha256(data).digest()

        resp = self.call(proto.FirmwareUpload(payload_hash=data_hash, payload=data))

        if isinstance(resp, proto.Success):
            return True

        elif isinstance(resp, proto.Failure) and resp.code == types.Failure_FirmwareError:
            return False

        raise Exception("Unexpected result %s" % resp)

class KeepKeyClient(ProtocolMixin, TextUIMixin, BaseClient):
    pass

class KeepKeyClientDebug(ProtocolMixin, TextUIMixin, DebugWireMixin, BaseClient):
    pass

class KeepKeyDebugClient(ProtocolMixin, DebugLinkMixin, DebugWireMixin, BaseClient):
    pass
