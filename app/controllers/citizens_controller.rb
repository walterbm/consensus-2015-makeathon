class CitizensController < ApplicationController
  before_action :authenticate_citizen!

  def index
  end

end
