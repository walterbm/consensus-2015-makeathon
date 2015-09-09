class CitizensController < ApplicationController
  before_action :authenticate_citizen!
  def show
  end

  def approve
    citizen = Citizen.find(params[:id])
    citizen.voted = true
    citizen.save
  end

  def reject
    citizen = Citizen.find(params[:id])
    citizen.voted = false
    citizen.save
  end

end
