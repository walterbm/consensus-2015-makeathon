var Contract = require("Contract");
var Solidity = require("Solidity");

var globalKeystore;
var voteCoinContract;

function getKeyStore(userObj,callback) {
        var oReq = new XMLHttpRequest();
        oReq.open("POST", "http://hacknet.blockapps.net/eth/v1.0/login", true);
        debugger;
        var params = "app="+encodeURIComponent(userObj.app)
                       +"&email="+encodeURIComponent(userObj.email)
                       +"&loginpass=" + encodeURIComponent(userObj.loginpass)
                       +"&address=" + encodeURIComponent(userObj.address);

        //Need to give time for wallet to be created
        for(var i=0; i<10000; i++)
          ;     
         // var params = "app=consensus-2015-makeathon"
         //               +"&email=craincharles@gmail.com"
         //               +"&loginpass=asdfg12345" 
         //               +"&address=2bf4868423232d54ac4fc155cd0783bb9e61f2d7";     

 
        oReq.setRequestHeader("Content-type", "application/x-www-form-urlencoded");

        oReq.onreadystatechange = function () {
          if (oReq.readyState == 4) {
            if (oReq.status === 200) {
               
              var jsonResp = JSON.parse(this.responseText);
              // assume we have ethlightjs
              console.log('retrieved: ' + jsonResp.encryptedWallet);
              keystore = ethlightjs.keystore.deserialize(jsonResp.encryptedWallet);

              callbackKeyStore(keystore, userObj);       
             } else {
              console.log("error: " +  oReq.statusText);
            }
          } 
        };

        console.log(params);
        oReq.send(params);
}

callbackKeyStore =  function (keystore, userObj) {
  //walletaddress.value=keystore.addresses[0];
  debugger;
  globalKeystore = keystore;
  //code = "contract test { function multiply(uint a) returns(uint d) { return a * 7; } }";
  code = "contract VoteCoin { address owner; address latestProposal; uint amount; function VoteCoin(){ owner = msg.sender; amount = 1; latestProposal = 0x0;} function returnCoin() returns (uint cAmount){ amount = 1; cAmount=1;} }"
  var privkey = keystore.exportPrivateKey(keystore.addresses[0], userObj.loginpass);
  var account = Contract({ privkey: privkey });
  globalAccount = account;
  account.sync("http://hacknet.blockapps.net", function(){
    console.log(account);
  });
  function submitCode(code) {
        // Constructs a Solidity code object
        console.log("about to submit contract");
        Solidity(code).toContract({ // Makes a contract from it
            apiURL:"http://hacknet.blockapps.net",
            fromAccount:account,
            value:0,
            gasPrice:1,
            gasLimit:3141592,
        }, deploySuccess) // Does this with the contract
  }  
  submitCode(code);
    
}



function deployVoteCoin(email,address, strongPass){
  var userObj = {
    app: "consensus-2015-makeathon",
    email: email,
    loginpass: strongPass,
    address: address
  };
  getKeyStore(userObj);
}

function deploySuccess(contract){
  voteCoinContract = contract;
  console.log('We did it!');
  voteCoinContract.call("http://hacknet.blockapps.net", function(result){
            console.log("the voteCoinContract vote result is: " + result);

            //createGoal(walletaddr,  "82714c607d2f14de60cbdaa465e3db756f0d72b6", 100, keyStorebruh);
        }, { funcName:'returnCoin', 
            fromAccount:globalAccount, 
            value:1, 
            gasPrice:1, 
            gasLimit:3141592}, {});
} 