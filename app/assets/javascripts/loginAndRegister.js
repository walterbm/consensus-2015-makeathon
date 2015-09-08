generate_account = function(strongPass) {

      //Generate the address of the new Wallet
      var randomSeed = ethlightjs.keystore.generateRandomSeed();
      var keystore = new ethlightjs.keystore(randomSeed, strongPass);
      var addr = keystore.generateNewAddress(strongPass);
      var key = keystore.serialize;
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
                $scope.turn_on_faucet(oReq.responseText);
                //callback(oReq.responseText);
             } else {
                console.log("error", oReq.statusText);
            }
          } 
        }
        oReq.send(params);
    }