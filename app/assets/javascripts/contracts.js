var Contract = require("Contract");
var Solidity = require("Solidity");

var globalKeystore;

function getKeyStore(userObj,callback) {
        var oReq = new XMLHttpRequest();
        oReq.open("POST", "http://hacknet.blockapps.net/eth/v1.0/login", true);

        var params = "app="+encodeURIComponent(userObj.app)
                       +"&email="+encodeURIComponent(userObj.email)
                       +"&loginpass=" + encodeURIComponent(userObj.loginpass)
                       +"&address=" + encodeURIComponent(userObj.address);     
 
        oReq.setRequestHeader("Content-type", "application/x-www-form-urlencoded");

        oReq.onreadystatechange = function () {
          if (oReq.readyState == 4) {
            if (oReq.status === 200) {
               
              var jsonResp = JSON.parse(this.responseText);
              // assume we have ethlightjs
              console.log('retrieved: ' + jsonResp.encryptedWallet);
              keystore = ethlightjs.keystore.deserialize(jsonResp.encryptedWallet);

              callback(keystore, userObj);       
             } else {
              console.log("error: " +  oReq.statusText);
            }
          } 
        };
        oReq.send(params);
}

callbackKeyStore =  function (keystore, userObj) {
  walletaddress.value=keystore.addresses[0];
  var privkey = keystore.exportPrivateKey(walletaddress, userObj.loginpass);
  var account = Contract({ privkey: privkey });
  account.sync("http://hacknet.blockapps.net", function(){
    console.log(account);
  });
    
};

function deployVoteCoin(email,address, strongPass){
  var userObj = {
    app: "consensus-2015-makeathon",
    email: email,
    loginpass: strongPass,
    address: address
  };
  getKeyStore(userObj);
}