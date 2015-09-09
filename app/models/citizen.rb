class Citizen < ActiveRecord::Base
  # Include default devise modules. Others available are:
  # :confirmable, :lockable, :timeoutable and :omniauthable
  devise :database_authenticatable, :registerable,
         :recoverable, :rememberable, :trackable, :validatable

  has_many :citizen_proposals
  has_many :proposals, through: :citizen_proposals

  include KeepKey::InstanceMethods

end
