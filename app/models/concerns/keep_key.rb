module KeepKey

  module InstanceMethods
    def keep_key
      # Renturns the KeepKey device_id to be used as a password and recover the private_key
      # not ideal but functional enough for a hackathon demonstration
      # device_id = AB5454E19563E1328EB5F2E7
      result = `python lib/python/keepkey.py`
      result = result.chomp
      result.empty? ? nil : result
    end
  end

end