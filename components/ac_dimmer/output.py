from esphome import pins
import esphome.codegen as cg
from esphome.components import output
import esphome.config_validation as cv
from esphome.const import CONF_ID, CONF_MIN_POWER, CONF_METHOD

# ESPHome removed CONF_INTERRUPT_METHOD in newer versions; keep compatibility
try:
    from esphome.const import CONF_INTERRUPT_METHOD
except ImportError:
    CONF_INTERRUPT_METHOD = "interrupt_method"

from esphome.core import CORE

CODEOWNERS = ["@glmnet"]

# Custom options for this component
CONF_DIAC_DRAIN_PIN = "diac_drain_pin"
CONF_GATE_PIN = "gate_pin"
CONF_ZERO_CROSS_PIN = "zero_cross_pin"
CONF_INIT_WITH_HALF_CYCLE = "init_with_half_cycle"
CONF_ZERO_MEANS_ZERO = "zero_means_zero"

ac_dimmer_ns = cg.esphome_ns.namespace("ac_dimmer")
AcDimmer = ac_dimmer_ns.class_("AcDimmer", output.FloatOutput, cg.Component)

DimMethod = ac_dimmer_ns.enum("DimMethod")
DIM_METHODS = {
    "LEADING_PULSE": DimMethod.DIM_METHOD_LEADING_PULSE,
    "LEADING": DimMethod.DIM_METHOD_LEADING,
    "TRAILING": DimMethod.DIM_METHOD_TRAILING,
}

InterruptMethod = ac_dimmer_ns.enum("InterruptMethod")
INTERRUPT_METHODS = {
    "FALLING": InterruptMethod.INTERRUPT_METHOD_FALLING,
    "RISING": InterruptMethod.INTERRUPT_METHOD_RISING,
    "ANY": InterruptMethod.INTERRUPT_METHOD_ANY,
    "CHANGE": InterruptMethod.INTERRUPT_METHOD_CHANGE,
}

CONFIG_SCHEMA = cv.All(
    output.FLOAT_OUTPUT_SCHEMA.extend(
        {
            cv.Required(CONF_ID): cv.declare_id(AcDimmer),

            # Your hardware pins
            cv.Required(CONF_GATE_PIN): pins.internal_gpio_output_pin_schema,
            cv.Required(CONF_DIAC_DRAIN_PIN): pins.internal_gpio_output_pin_schema,
            cv.Required(CONF_ZERO_CROSS_PIN): pins.internal_gpio_input_pin_schema,

            # Existing options
            cv.Optional(CONF_INIT_WITH_HALF_CYCLE, default=True): cv.boolean,
            cv.Optional(CONF_METHOD, default="LEADING_PULSE"): cv.enum(
                DIM_METHODS, upper=True, space="_"
            ),

            # Custom options used in your YAML
            cv.Optional(CONF_INTERRUPT_METHOD, default="ANY"): cv.enum(
                INTERRUPT_METHODS, upper=True, space="_"
            ),
            cv.Optional(CONF_ZERO_MEANS_ZERO, default=False): cv.boolean,
        }
    ).extend(cv.COMPONENT_SCHEMA),
)


async def to_code(config):
    if CORE.is_esp8266:
        # If your Arduino ESP8266 build needs waveform generator, keep this
        from esphome.components.esp8266.const import require_waveform
        require_waveform()

    var = cg.new_Pvariable(config[CONF_ID])
    await cg.register_component(var, config)

    # override default min power to 10%
    if CONF_MIN_POWER not in config:
        config[CONF_MIN_POWER] = 0.1
    await output.register_output(var, config)

    gate = await cg.gpio_pin_expression(config[CONF_GATE_PIN])
    cg.add(var.set_gate_pin(gate))

    diac = await cg.gpio_pin_expression(config[CONF_DIAC_DRAIN_PIN])
    cg.add(var.set_diac_drain_pin(diac))

    zc = await cg.gpio_pin_expression(config[CONF_ZERO_CROSS_PIN])
    cg.add(var.set_zero_cross_pin(zc))

    cg.add(var.set_init_with_half_cycle(config[CONF_INIT_WITH_HALF_CYCLE]))
    cg.add(var.set_method(config[CONF_METHOD]))

    # These setters must exist in your C++ class (you already added diac pin earlier)
    cg.add(var.set_interrupt_method(config[CONF_INTERRUPT_METHOD]))
    cg.add(var.set_zero_means_zero(config[CONF_ZERO_MEANS_ZERO]))
