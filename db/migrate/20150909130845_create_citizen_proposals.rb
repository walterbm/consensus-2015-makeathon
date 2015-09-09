class CreateCitizenProposals < ActiveRecord::Migration
  def change
    create_table :citizen_proposals do |t|
      t.integer :citizen_id
      t.integer :proposal_id
    end
  end
end
