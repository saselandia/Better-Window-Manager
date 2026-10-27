.pragma library

// os-release is data, never shell code. Accept quoted and unquoted values;
// Gentoo uses single quotes, while many other distros use double quotes.
function parse(text) {
    const data = {};
    for (const line of String(text || "").split(/\r?\n/)) {
        const match = line.match(/^\s*([A-Z][A-Z0-9_]*)=(.*)$/);
        if (!match) continue;
        let value = match[2].trim();
        if (value.length >= 2 && value[0] === "'" && value[value.length - 1] === "'")
            value = value.slice(1, -1);
        else if (value.length >= 2 && value[0] === '"' && value[value.length - 1] === '"')
            value = value.slice(1, -1).replace(/\\(["\\$`])/g, "$1");
        else
            value = value.replace(/\\(.)/g, "$1");
        data[match[1]] = value;
    }
    return data;
}

function icon(id, idLike) {
    const icons = {
        artix: "arch", arch: "arch", manjaro: "manjaro", endeavouros: "endeavouros",
        cachyos: "cachyos", nixos: "nixos", fedora: "fedora", linuxmint: "ubuntu",
        ubuntu: "ubuntu", zorin: "ubuntu", pop: "ubuntu", popos: "ubuntu",
        debian: "debian", raspbian: "debian", kali: "debian", funtoo: "gentoo", gentoo: "gentoo"
    };
    for (const candidate of [id].concat(String(idLike || "").split(/\s+/))) {
        const key = String(candidate || "").toLowerCase();
        if (icons[key]) return icons[key] + "-symbolic";
    }
    return "linux-symbolic";
}
