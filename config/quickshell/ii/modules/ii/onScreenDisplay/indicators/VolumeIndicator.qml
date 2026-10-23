import qs.services
import QtQuick
import qs.modules.ii.onScreenDisplay

OsdValueIndicator {
    id: osdValues
    value: Audio.sink?.audio.volume ?? 0
    icon: Audio.sink?.audio.muted ? "volume_off" : "volume_up"
    name: Translation.tr("Volume")
    breezeMuted: Audio.sink?.audio.muted ?? false
    breezeIcon: {
        const v = value;
        if (breezeMuted || v <= 0) return "audio-volume-muted";
        if (v > 1.0) return "audio-volume-high-warning";
        return v < 0.34 ? "audio-volume-low" : (v < 0.67 ? "audio-volume-medium" : "audio-volume-high");
    }
}
