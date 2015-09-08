class AddPublicKeytoCitizens < ActiveRecord::Migration
  def change
    add_column :citizens, :publicrkey, :string
  end
end
