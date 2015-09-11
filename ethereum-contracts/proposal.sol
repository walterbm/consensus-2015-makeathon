contract Proposal {
    address owner;
    uint numberOfVoters;
    uint totalVotes;
    uint yesVote;
    uint noVote;
    uint done;
    address voters;
    
    
    function Proposal(){
        owner = msg.sender;
        numberOfVoters = 5;
        yesVote = 0;
        noVote = 0;
        totalVotes = 0;
        
        mapping (uint => address) voters;
    }
    
    // function vote() returns (uint voted){
    //     voters[totalVotes] = msg.sender
    //     totalVotes++;
    //     numberOfVoters
    //     if(totalVotes)
    // }
    
    function vote(uint vote) returns (uint voted){
        if(vote == 1){
            yesVote++;
        }else{
            noVote++;
        }
        voted = 1;
    }
    
    function yesVotes() returns (uint totalYes){
        totalYes = yesVote;
    }
    
    function noVotes() returns (uint totalNo){
        totalNo = noVote;
    }
    function returnVotes() returns (uint amount){
        amount = yesVote + noVote;
    }
}

