class Trait:
    def __init__(self, name, description, nature, numeric_effects=None, multiplier_effects=None):
        self.name = name
        self.description = description
        self.nature = nature
        self.numeric_effects = numeric_effects if numeric_effects else {}
        self.multiplier_effects = multiplier_effects if multiplier_effects else {}

    def apply_numeric_effects(self, carrier):
        for attr, value in self.numeric_effects.items():
            if hasattr(carrier, attr):
                old_value = getattr(carrier, attr)
                new_value = old_value + value
                setattr(carrier, attr, new_value)
                print(f"特质 '{self.name}' 应用: {carrier.name} 的 {attr} 增加了 {value} 点, 从 {old_value} 变为 {new_value}")

    def apply_multiplier_effects(self, carrier):
        for attr, multiplier in self.multiplier_effects.items():
            if hasattr(carrier, attr):
                old_value = getattr(carrier, attr)
                new_value = old_value * (1 + multiplier)
                setattr(carrier, attr, new_value)
                print(f"特质 '{self.name}' 应用: {carrier.name} 的 {attr} 提升了 {multiplier * 100}%, 从 {old_value} 变为 {new_value}")

    def apply(self, carrier):
        print(f"Applying trait '{self.name}' to {carrier.name}")
        self.apply_numeric_effects(carrier)
        self.apply_multiplier_effects(carrier)

    def __str__(self):
        return f"{self.name}: {self.description}"