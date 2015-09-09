class CitizenProposal < ActiveRecord::Base
  belongs_to :citizen
  belongs_to :proposal
end
