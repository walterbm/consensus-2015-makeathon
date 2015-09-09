module KeepKey

  module InstanceMethods
    def keep_key
      result = `python lib/python/keepkey.py`
      result.chomp
      result.empty? ? nil : result
    end
  end

end