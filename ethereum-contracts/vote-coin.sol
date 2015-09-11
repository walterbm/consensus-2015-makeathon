contract VoteCoin {
    address owner;
    address latestProposal;
    uint amount;
    
    function VoteCoin(){
        owner = msg.sender;
        amount = 1;
        latestProposal = 0x0;
    }
    
    //check to see if can vote and 
    function vote(uint decision ,address proposal) returns (uint voted){
        if(msg.sender == owner && amount > 0){
            proposal.call('vote',decision);
            amount = 0;
            voted = 1;
        }else{
            voted = 0;
        }
    }
    
    function returnCoin(){
        amount = 1;
    }
}