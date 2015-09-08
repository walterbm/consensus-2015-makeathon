class AddPublicKeytoCitizensAgain < ActiveRecord::Migration
  def change
    add_column :citizens, :public_key, :string
  end
end
