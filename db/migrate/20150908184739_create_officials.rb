class CreateOfficials < ActiveRecord::Migration
  def change
    create_table :officials do |t|
      t.string :name
      t.string :position
      t.string :organization
      t.timestamps null: false
    end
  end
end
