class RenameColInOfficials < ActiveRecord::Migration
  def change
    rename_column :officials, :publicrkey, :public_key
  end
end
