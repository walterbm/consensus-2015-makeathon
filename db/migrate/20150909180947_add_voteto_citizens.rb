class AddVotetoCitizens < ActiveRecord::Migration
  def change
    add_column :citizens, :voted, :boolean 
  end
end
