class AddGovOfficialsToCitizens < ActiveRecord::Migration
  def change
    add_column :citizens, :elected_official, :boolean, :default => false
  end
end
