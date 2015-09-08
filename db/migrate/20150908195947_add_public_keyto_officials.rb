class AddPublicKeytoOfficials < ActiveRecord::Migration
  def change
    add_column :officials, :publicrkey, :string
  end
end
