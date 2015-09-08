generate_account = function(strongPass) {

      //Generate the address of the new Wallet
      var randomSeed = ethlightjs.keystore.generateRandomSeed();
      var keystore = new ethlightjs.keystore(randomSeed, strongPass);
      var addr = keystore.generateNewAddress(strongPass);
      var key = keystore.serialize();
      return [addr, key];
      
}

create_user = function(email, password, address, key){
      var oReq = new XMLHttpRequest();
        oReq.open("POST", "http://hacknet.blockapps.net/eth/v1.0/wallet", true);
        var user_object = {
            app: "consensus-2015-makeathon",
            email: email,
            loginpass: password,
            address: address,
            enckey: key
          };

        var params = "app="+encodeURIComponent(user_object.app)
                       +"&email="+encodeURIComponent(user_object.email)
                       +"&loginpass=" + encodeURIComponent(user_object.loginpass)
                       +"&address=" + encodeURIComponent(user_object.address)
                       +"&enckey=" + encodeURIComponent(user_object.enckey);
 
 
        console.log("params: " + params);
        oReq.setRequestHeader("Content-type", "application/x-www-form-urlencoded");

        oReq.onreadystatechange = function () {
          if (oReq.readyState == 4) {
            if (oReq.status === 200) {
                console.log(oReq.responseText);
                turnOnFaucet(oReq.responseText);
                //callback(oReq.responseText);
             } else {
                console.log("error", oReq.statusText);
            }
          } 
        };
        oReq.send(params);
    };

turnOnFaucet =  function (res) {

    data = JSON.parse(res);
    console.log("wallet: " + data.encryptedWallet);
    console.log("addresses: " + JSON.parse(data.encryptedWallet).addresses);

    var faucetAddr = JSON.parse(data.encryptedWallet).addresses;
    var oReq = new XMLHttpRequest();
    
    var apiURL = "http://hacknet.blockapps.net";
    oReq.open("POST", apiURL + "/eth/v1.0/faucet", true);
    var params = "address=" + encodeURIComponent(faucetAddr);
    oReq.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    oReq.onload = function () {
      if (oReq.readyState == 4 && oReq.status == 200) {
        console.log("faucet should have worked");
      } else { 
        console.log("error");
      }
    }
    console.log("sending faucet request");
    oReq.send(params);
    console.log("faucet request sent");

    return JSON.parse(data.encryptedWallet).addresses;
}