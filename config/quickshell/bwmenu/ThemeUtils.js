.pragma library

function ink(color) {
    function linear(value) { return value <= 0.04045 ? value / 12.92 : Math.pow((value + 0.055) / 1.055, 2.4); }
    const luminance = 0.2126 * linear(color.r) + 0.7152 * linear(color.g) + 0.0722 * linear(color.b);
    return luminance > 0.179 ? "#000000" : "#ffffff";
}

function mix(first, second, amount) {
    return Qt.rgba(first.r * (1-amount) + second.r * amount,
                   first.g * (1-amount) + second.g * amount,
                   first.b * (1-amount) + second.b * amount, 1);
}
