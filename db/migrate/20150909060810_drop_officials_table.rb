class DropOfficialsTable < ActiveRecord::Migration
  def change
    drop_table :officials
  end
end
