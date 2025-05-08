class ScannedDevice:
  pass

class Parser:
  @classmethod
  def parse(cls, device, advertisement_data, existing: list[ScannedDevice]) -> ScannedDevice|None:
    raise NotImplementedError