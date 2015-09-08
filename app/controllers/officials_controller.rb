class OfficialsController < ApplicationController
  before_action :authenticate_official!

  def index
  end

end
