class CreateCitizens < ActiveRecord::Migration
  def change
    create_table :citizens do |t|
      t.string :name
      t.string :organization
      t.timestamps null: false
    end
  end
end
