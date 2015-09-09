class CitizensController < ApplicationController
  before_action :authenticate_citizen!

end
