"""GPIOZero backend for the verified Pi 5 Bookworm classroom image.

Importing this module does not open a chip or request a GPIO line. Call
``create_header_factory`` before constructing any GPIOZero device, then pass
the returned factory as ``pin_factory=...`` or assign it to Device.pin_factory.

Discovery and ``--inspect`` only open GPIO chip handles, read chip metadata,
and close the handles. They never claim/configure GPIO lines.

The compatibility subclass is deliberately restricted to the versions tested
on the teaching Pi. It does not patch installed packages or /dev aliases.
Only metadata/close behavior has been verified; attached hardware is required
to verify actual LED, button, and ultrasonic operation.
"""

from importlib.metadata import version
from pathlib import Path

import lgpio
from gpiozero.pins.lgpio import LGPIOFactory, LGPIOPin
from gpiozero.pins.local import LocalPiFactory


def find_rp1_chip():
    """Find exactly one header controller by its kernel label, never its number."""
    matches = []
    errors = []
    devices = sorted(Path('/dev').glob('gpiochip*'), key=lambda path: path.name)
    for device in devices:
        suffix = device.name.removeprefix('gpiochip')
        if not suffix.isdecimal():
            continue
        handle = None
        try:
            chip = int(suffix)
            handle = lgpio.gpiochip_open(chip)
            status, lines, name, label = lgpio.gpio_get_chip_info(handle)
            if status == 0 and label == 'pinctrl-rp1':
                matches.append((chip, lines, name, label))
        except (OSError, lgpio.error) as exc:
            errors.append(f'{device.name}: {exc}')
        finally:
            if handle is not None:
                lgpio.gpiochip_close(handle)
    if len(matches) != 1:
        detail = '; '.join(errors) or 'no chip access errors'
        raise RuntimeError(
            f'Expected one pinctrl-rp1 chip, found {len(matches)}. {detail}')
    return matches[0]


class _BookwormLGPIOFactory(LGPIOFactory):
    """Preserve LGPIOFactory behavior while honoring its explicit chip argument."""

    def __init__(self, chip):
        if (version('gpiozero'), version('lgpio')) not in {
            ('2.0.1', '0.2.2'), ('2.0.1', '0.2.2.0')
        }:
            raise RuntimeError('Compatibility backend has not been reviewed for these versions')
        # This is the immediate parent of the installed LGPIOFactory. It also
        # preserves LocalPiFactory's shared pin and reservation dictionaries.
        LocalPiFactory.__init__(self)
        self._handle = None
        self._chip = chip
        self.pin_class = LGPIOPin
        self._handle = lgpio.gpiochip_open(chip)


def create_header_factory():
    """Select RP1, preferring the unmodified public LGPIOFactory constructor."""
    # close() on a LocalPiFactory closes its shared pin objects. The helper
    # therefore runs only before any local GPIOZero pins have been created.
    if LocalPiFactory.pins:
        raise RuntimeError('Select the GPIO backend before constructing GPIOZero devices')
    chip, _lines, _name, _label = find_rp1_chip()
    factory = None
    try:
        factory = LGPIOFactory(chip=chip)
    except (OSError, lgpio.error):
        # The verified Bookworm constructor may ignore chip and try missing 0/4.
        pass
    if factory is not None:
        if factory.chip == chip:
            return factory
        factory.close()
    return _BookwormLGPIOFactory(chip)


def inspect_backend():
    """Validate metadata/close behavior, without allocating a single pin."""
    selected = find_rp1_chip()
    factory = create_header_factory()
    try:
        print('gpiozero:', version('gpiozero'))
        print('lgpio:', version('lgpio'))
        print('detected chip metadata:', selected)
        print('factory class:', type(factory).__name__)
        print('factory chip:', factory.chip)
        print('open handle metadata:', lgpio.gpio_get_chip_info(factory._handle))
        print('created GPIOZero pins:', len(factory.pins))
        assert factory.chip == selected[0]
        assert not factory.pins
    finally:
        factory.close()
    assert factory._handle is None
    factory.close()  # Verify the inherited close is idempotent.
    print('metadata-only verification passed; no GPIO lines requested')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inspect', action='store_true', required=True)
    parser.parse_args()
    inspect_backend()
