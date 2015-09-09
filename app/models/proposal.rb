class Proposal < ActiveRecord::Base

  has_many :citizen_proposals
  has_many :citizens, through: :citizen_proposals

end
