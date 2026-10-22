// SPDX-FileCopyrightText: 2026 Tim Wiederhake
//
// SPDX-License-Identifier: WTFPL

module leds(
    output wire [5:0] nLed
);

// LED5..LED0: active low; invert the original pattern.
assign nLed = 6'b101100;

endmodule

