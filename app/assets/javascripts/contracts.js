var Contract = require("Contract");
var Solidity = require("Solidity");

var proposal = [244, 211, 47, 139, 78, 92, 24, 36, 80, 255, 151, 200, 38, 144, 31, 96, 12, 93, 164, 157];
var globalKeystore;
var globalAddress;
var voteCoinContract;

function getKeyStore(userObj,callback) {
        var oReq = new XMLHttpRequest();
        oReq.open("POST", "http://hacknet.blockapps.net/eth/v1.0/login", true);
        // debugger;
        var params = "app="+encodeURIComponent(userObj.app)
                       +"&email="+encodeURIComponent(userObj.email)
                       +"&loginpass=" + encodeURIComponent(userObj.loginpass)
                       +"&address=" + encodeURIComponent(userObj.address);

        //Need to give time for wallet to be created
         
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
               for(var i=0; i<100000; i++)
                  ;   
              callback(keystore, userObj);       
             } else {
              console.log("error: " +  oReq.statusText);
            }
          } 
        };

        console.log(params);
        // for(var i=0; i<10000000; i++)
        //     ; 
        debugger;
        oReq.send(params);
        
}

callbackKeyStoreCreate =  function (keystore, userObj) {
  //walletaddress.value=keystore.addresses[0];
  //debugger;
  globalKeystore = keystore;
  //code = "contract test { function multiply(uint a) returns(uint d) { return a * 7; } }";
  code = "contract VoteCoin { address owner; address latestProposal; uint amount; function VoteCoin(){ owner = msg.sender; amount = 1; latestProposal = 0x0;} function vote(uint decision ,address proposal) returns (uint voted){ if(msg.sender == owner && amount > 0){ proposal.call('vote',decision); amount = 0; voted = 1; }else{ voted = 0; } } function returnCoin() returns (uint cAmount){ amount = 1; cAmount=1;} }";
  var privkey = keystore.exportPrivateKey(keystore.addresses[0], userObj.loginpass);
  var account = Contract({ privkey: privkey });
  globalAccount = account;
  account.sync("http://hacknet.blockapps.net", function(){
    console.log(account);
  });
  function submitCode(code) {
        // Constructs a Solidity code object
        console.log("about to submit contract");
        var contractProto = Solidity(code);
        // debugger;
        contractProto.toContract({ // Makes a contract from it
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
  getKeyStore(userObj,callbackKeyStoreCreate);
}

function deploySuccess(contract){

  //need to ge
  voteCoinContract = contract;
  globalAddress = contract.address;
  console.log('We did it!');
  // voteCoinContract.call("http://hacknet.blockapps.net", function(result){
  //           console.log("the voteCoinContract vote result is: " + result);

  //           //createGoal(walletaddr,  "82714c607d2f14de60cbdaa465e3db756f0d72b6", 100, keyStorebruh);
  //       }, { funcName:'returnCoin', 
  //           fromAccount:globalAccount, 
  //           value:1, 
  //           gasPrice:1, 
  //           gasLimit:3141592}, {});
  vote(1);
} 

function deployProposal(email,address, strongPass){
  var userObj = {
    app: "consensus-2015-makeathon",
    email: email,
    loginpass: strongPass,
    address: address
  };
  getKeyStore(userObj,callbackProposal);
}

function callbackProposal(keystore, userObj){
  //code = "contract test { function multiply(uint a) returns(uint d) { return a * 7; } }";
  code = "contract Proposal { address owner; uint numberOfVoters;uint totalVotes;uint yesVote; uint noVote; uint done; address voters; function Proposal(){ owner = msg.sender; numberOfVoters = 5; yesVote = 0; noVote = 0; totalVotes = 0; mapping (uint => address) voters; } function vote(uint vote) returns (uint voted){ if(vote == 1){ yesVote++;}else{ noVote++; } voted = 1; } function yesVotes() returns (uint totalYes){ totalYes = yesVote;}function noVotes() returns (uint totalNo){ totalNo = noVote; } function returnVotes() returns (uint amount){ amount = yesVote + noVote; } }";
  var privkey = keystore.exportPrivateKey(keystore.addresses[0], userObj.loginpass);
  var account = Contract({ privkey: privkey });
  globalAccount = account;
  account.sync("http://hacknet.blockapps.net", function(){
    console.log(account);
  });
  function submitCode(code) {
        // Constructs a Solidity code object
        console.log("about to submit contract");
        var contractProto = Solidity(code);
        //debugger;
        contractProto.toContract({ // Makes a contract from it
            apiURL:"http://hacknet.blockapps.net",
            fromAccount:account,
            value:0,
            gasPrice:1,
            gasLimit:3141592,
        }, deployProposalSuccess) // Does this with the contract
  }  
  submitCode(code);
}

function deployProposalSuccess(contract){
  console.log(contract.address);
}

function vote(decision){
  voteCoinContract.call("http://hacknet.blockapps.net", function(result){
            console.log("the voteCoinContract vote result is: " + result);

            //createGoal(walletaddr,  "82714c607d2f14de60cbdaa465e3db756f0d72b6", 100, keyStorebruh);
        }, { funcName:'vote', 
            fromAccount:globalAccount, 
            value:1, 
            gasPrice:1, 
            gasLimit:3141592}, {decision:decision, proposal:proposal});
}
// function getContract(email, address, strongPass){
//   var userObj = {
//     app: "consensus-2015-makeathon",
//     email: email,
//     loginpass: strongPass,
//     address: address
//   };
//   getKeyStore(userObj,callbackGetContract);
// }

// function callbackGetContract(keystore, userObj, address){
//   code = "contract VoteCoin { address owner; address latestProposal; uint amount; function VoteCoin(){ owner = msg.sender; amount = 1; latestProposal = 0x0;} function returnCoin() returns (uint cAmount){ amount = 1; cAmount=1;} }";
//   var contract = Solidity.attach({code:code,name:'' ,vmCode: undefined, symbTab:undefined ,address:[address]} );

// }