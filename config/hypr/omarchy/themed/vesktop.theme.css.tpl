/**
 * @name BWM Omarchy TUI
 * @author BWM
 * @version 2.0.0
 * @description Estilo Retro de BWM: Discord como una terminal de Omarchy (monoespaciada, sin redondeos, paneles enmarcados, selección invertida). Colores del tema Retro activo.
 */

/* ==============================================================================
 * Omarchy no tematiza Discord (es una web app) y omarchy-theme-hook sólo cambia colores
 * cargando un CSS remoto; este tema es propio de BWM y se genera con cada tema Retro
 * (bwm_omarchy.apply_vesktop) desde ~/.local/state/bwm/omarchy/colors.toml.
 * ============================================================================== */

:root, .theme-dark, .theme-light, [class*="theme-dark"], [class*="theme-light"], html, body {
    --bwm-bg: {{ background }};
    --bwm-bg-dark: {{ dark_background }};
    --bwm-bg-darker: {{ darker_background }};
    --bwm-bg-light: {{ lighter_background }};
    --bwm-fg: {{ foreground }};
    --bwm-fg-dim: {{ dark_foreground }};
    --bwm-fg-bright: {{ bright_foreground }};
    --bwm-muted: {{ muted }};
    --bwm-accent: {{ accent }};
    --bwm-selection: {{ selection }};
    --bwm-red: {{ red }};
    --bwm-green: {{ green }};
    --bwm-yellow: {{ yellow }};
    --bwm-blue: {{ blue }};
    --bwm-cyan: {{ cyan }};
    --bwm-magenta: {{ magenta }};
    /* Fallbacks for symbols and kaomoji the monospace font lacks, then colour emoji */
    --bwm-font: "JetBrainsMono Nerd Font", "Noto Sans Mono", "DejaVu Sans Mono", "Noto Sans",
        "Noto Sans Symbols 2", "Noto Sans Symbols", "DejaVu Sans", "FreeSerif", "Noto Color Emoji", monospace;

    /* Fondos (variables actuales de Discord y las clásicas) */
    --bg-base-primary: var(--bwm-bg) !important;
    --bg-base-secondary: var(--bwm-bg-dark) !important;
    --bg-base-tertiary: var(--bwm-bg-darker) !important;
    --bg-surface-raised: var(--bwm-bg-light) !important;
    --bg-surface-raised-hover: var(--bwm-selection) !important;
    --bg-surface-overlay: var(--bwm-bg-dark) !important;
    --bg-surface-overlay-tmp: var(--bwm-bg-dark) !important;
    --bg-mod-faint: color-mix(in srgb, var(--bwm-accent) 6%, transparent) !important;
    --bg-mod-subtle: color-mix(in srgb, var(--bwm-accent) 10%, transparent) !important;
    --bg-mod-strong: color-mix(in srgb, var(--bwm-accent) 18%, transparent) !important;
    --bg-brand: var(--bwm-accent) !important;
    --background-base-lowest: var(--bwm-bg-darker) !important;
    --background-base-lower: var(--bwm-bg-dark) !important;
    --background-base-low: var(--bwm-bg-dark) !important;
    --background-surface-high: var(--bwm-bg-light) !important;
    --background-surface-higher: var(--bwm-bg-light) !important;
    --background-surface-highest: var(--bwm-selection) !important;
    --background-primary: var(--bwm-bg) !important;
    --background-secondary: var(--bwm-bg-dark) !important;
    --background-secondary-alt: var(--bwm-bg-dark) !important;
    --background-tertiary: var(--bwm-bg-darker) !important;
    --background-accent: var(--bwm-selection) !important;
    --background-floating: var(--bwm-bg-dark) !important;
    --background-nested-floating: var(--bwm-bg-dark) !important;
    --background-mobile-primary: var(--bwm-bg) !important;
    --background-mobile-secondary: var(--bwm-bg-dark) !important;
    --background-modifier-hover: color-mix(in srgb, var(--bwm-accent) 8%, transparent) !important;
    --background-modifier-active: color-mix(in srgb, var(--bwm-accent) 14%, transparent) !important;
    --background-modifier-selected: var(--bwm-selection) !important;
    --background-modifier-accent: var(--bwm-muted) !important;
    --background-message-hover: color-mix(in srgb, var(--bwm-accent) 5%, transparent) !important;
    --background-mentioned: color-mix(in srgb, var(--bwm-yellow) 8%, transparent) !important;
    --background-mentioned-hover: color-mix(in srgb, var(--bwm-yellow) 12%, transparent) !important;
    --channeltextarea-background: var(--bwm-bg-darker) !important;
    --input-background: var(--bwm-bg-darker) !important;
    --modal-background: var(--bwm-bg) !important;
    --modal-footer-background: var(--bwm-bg-dark) !important;
    --chat-background-default: var(--bwm-bg) !important;
    --home-background: var(--bwm-bg) !important;
    --activity-card-background: var(--bwm-bg-dark) !important;
    --deprecated-card-bg: var(--bwm-bg-dark) !important;
    --card-primary-bg: var(--bwm-bg-dark) !important;
    --card-secondary-bg: var(--bwm-bg-dark) !important;
    --embed-background: var(--bwm-bg-dark) !important;
    --scrollbar-auto-thumb: var(--bwm-muted) !important;
    --scrollbar-auto-track: transparent !important;
    --scrollbar-thin-thumb: var(--bwm-muted) !important;
    --scrollbar-thin-track: transparent !important;

    /* Acento */
    --brand-500: var(--bwm-accent) !important;
    --brand-560: var(--bwm-accent) !important;
    --brand-600: var(--bwm-accent) !important;
    --brand-experiment: var(--bwm-accent) !important;
    --brand-experiment-500: var(--bwm-accent) !important;
    --brand-experiment-560: var(--bwm-accent) !important;
    --brand-experiment-600: var(--bwm-accent) !important;
    --control-brand-foreground: var(--bwm-accent) !important;
    --control-brand-foreground-new: var(--bwm-accent) !important;

    /* Texto */
    --header-primary: var(--bwm-fg-bright) !important;
    --header-secondary: var(--bwm-fg-dim) !important;
    --text-default: var(--bwm-fg) !important;
    --text-normal: var(--bwm-fg) !important;
    --text-primary: var(--bwm-fg) !important;
    --text-secondary: var(--bwm-fg-dim) !important;
    --text-tertiary: var(--bwm-fg-dim) !important;
    --text-muted: var(--bwm-fg-dim) !important;
    --text-strong: var(--bwm-fg-bright) !important;
    --text-link: var(--bwm-cyan) !important;
    --text-brand: var(--bwm-accent) !important;
    --text-positive: var(--bwm-green) !important;
    --text-warning: var(--bwm-yellow) !important;
    --text-danger: var(--bwm-red) !important;
    --channels-default: var(--bwm-fg-dim) !important;
    --channel-icon: var(--bwm-fg-dim) !important;
    --interactive-normal: var(--bwm-fg-dim) !important;
    --interactive-hover: var(--bwm-fg) !important;
    --interactive-active: var(--bwm-accent) !important;
    --interactive-muted: var(--bwm-muted) !important;
    --icon-default: var(--bwm-fg-dim) !important;
    --icon-strong: var(--bwm-fg) !important;

    /* Bordes, estados */
    --border-faint: var(--bwm-muted) !important;
    --border-subtle: var(--bwm-muted) !important;
    --border-normal: var(--bwm-muted) !important;
    --border-strong: var(--bwm-accent) !important;
    --status-positive: var(--bwm-green) !important;
    --status-online: var(--bwm-green) !important;
    --status-idle: var(--bwm-yellow) !important;
    --status-dnd: var(--bwm-red) !important;
    --status-offline: var(--bwm-muted) !important;
    --status-warning: var(--bwm-yellow) !important;
    --status-danger: var(--bwm-red) !important;
    --info-positive-foreground: var(--bwm-green) !important;
    --info-warning-foreground: var(--bwm-yellow) !important;
    --info-danger-foreground: var(--bwm-red) !important;
    --button-danger-background: var(--bwm-red) !important;
    --button-positive-background: var(--bwm-green) !important;
    --mention-foreground: var(--bwm-yellow) !important;
    --mention-background: color-mix(in srgb, var(--bwm-yellow) 15%, transparent) !important;

    /* Tipografía y formas */
    --font-primary: var(--bwm-font) !important;
    --font-display: var(--bwm-font) !important;
    --font-headline: var(--bwm-font) !important;
    --font-code: var(--bwm-font) !important;
    --radius-xs: 0 !important; --radius-sm: 0 !important; --radius-md: 0 !important;
    --radius-lg: 0 !important; --radius-xl: 0 !important; --radius-xxl: 0 !important;
    --radius-round: 0 !important; --custom-border-radius: 0 !important;
    --elevation-low: none !important; --elevation-medium: none !important;
    --elevation-high: none !important; --elevation-stroke: none !important;
    --shadow-low: none !important; --shadow-medium: none !important; --shadow-high: none !important;
}

/* ------------------------------------------------------------------ Base */
*, *::before, *::after {
    font-family: var(--bwm-font) !important;
    border-radius: 0 !important;
    box-shadow: none;
    text-shadow: none !important;
}
#app-mount, [class*="app_"], [class*="appMount_"], [class*="bg_"], [class*="base_"] {
    background: var(--bwm-bg) !important;
}
[class*="avatarDecoration"], [class*="bannerSVGWrapper"], [class*="profileEffects"],
[class*="nameplate"], [class*="upsell"], [class*="premiumPromo"], [class*="giftButton"],
[class*="nitroWheel"] {
    display: none !important;
}
::selection { background: var(--bwm-accent); color: var(--bwm-bg); }

/* Avatares, iconos de servidor y puntos de estado cuadrados */
img, [class*="avatar"], [class*="icon_"], [class*="wrapper_"] svg foreignObject {
    border-radius: 0 !important;
}
svg mask rect, svg mask circle { rx: 0 !important; }

/* ------------------------------------------------------------------ Paneles (ventanas de una terminal) */
nav[class*="guilds_"], [class*="guilds_"] [class*="scroller_"] {
    background: var(--bwm-bg-darker) !important;
    border-right: 1px solid var(--bwm-muted) !important;
}
div[class*="sidebar_"], nav[class*="sidebar_"], [class*="sidebar_"] [class*="scroller_"],
[class*="privateChannels_"] {
    background: var(--bwm-bg-dark) !important;
}
div[class*="sidebar_"] { border-right: 1px solid var(--bwm-muted) !important; }
[class*="membersWrap_"], [class*="members_"], aside[class*="profilePanel"] {
    background: var(--bwm-bg-dark) !important;
    border-left: 1px solid var(--bwm-muted) !important;
}
main[class*="chatContent_"], div[class*="chat_"] { background: var(--bwm-bg) !important; }
section[class*="title_"], header[class*="header_"], [class*="upperContainer_"],
[class*="container_"][class*="themed_"] {
    background: var(--bwm-bg-dark) !important;
    border-bottom: 1px solid var(--bwm-muted) !important;
}
section[class*="panels_"] {
    background: var(--bwm-bg-darker) !important;
    border-top: 1px solid var(--bwm-muted) !important;
}
/* The account box: flat, no nameplate/banner art behind it */
section[class*="panels_"] *, section[class*="panels_"] *::before, section[class*="panels_"] *::after {
    background-image: none !important;
}
section[class*="panels_"] > div, section[class*="panels_"] [class*="container_"],
section[class*="panels_"] [class*="wrapper_"]:not([class*="avatar"]) {
    background-color: var(--bwm-bg-darker) !important;
    border: 0 !important;
    box-shadow: none !important;
    margin: 0 !important;
}
section[class*="panels_"] video, section[class*="panels_"] img[class*="nameplate"],
section[class*="panels_"] [class*="videoContainer"], section[class*="panels_"] [class*="backdrop"] {
    display: none !important;
}

/* Cabeceras de categoría como títulos de panel de TUI: ── CANALES ── */
[class*="containerDefault_"] h3, [class*="mainContent_"] h3[class*="name_"],
h2[class*="membersGroup_"], [class*="membersGroup_"] {
    color: var(--bwm-accent) !important;
    text-transform: uppercase !important;
    letter-spacing: .08em !important;
}
h2[class*="membersGroup_"]::before { content: "── "; color: var(--bwm-muted); }

/* ------------------------------------------------------------------ Selección invertida (como en una TUI) */
[class*="modeSelected_"] [class*="link_"], [class*="selected_"] > [class*="link_"],
[class*="interactiveSelected_"], [class*="selected_"][class*="interactive_"],
[class*="channel_"][class*="selected_"] [class*="interactive_"] {
    background: var(--bwm-accent) !important;
    box-shadow: none !important;
}
[class*="modeSelected_"] [class*="link_"] *, [class*="selected_"] > [class*="link_"] *,
[class*="interactiveSelected_"] *, [class*="channel_"][class*="selected_"] [class*="interactive_"] * {
    color: var(--bwm-bg) !important;
    fill: var(--bwm-bg) !important;
}
[class*="link_"]:hover, [class*="interactive_"]:hover {
    background: color-mix(in srgb, var(--bwm-accent) 10%, transparent) !important;
}
[class*="modeUnread_"] [class*="name_"] { color: var(--bwm-fg-bright) !important; }
[class*="unread_"] { background: var(--bwm-accent) !important; width: 3px !important; }
[class*="pill_"] [class*="item_"] { background: var(--bwm-accent) !important; border-radius: 0 !important; }

/* ------------------------------------------------------------------ Mensajes */
[class*="username_"] { color: var(--bwm-accent); font-weight: 700 !important; }
[class*="timestamp_"], [class*="timestamp_"] time { color: var(--bwm-fg-dim) !important; }
[class*="messageListItem"] [class*="message_"]:hover { background: var(--background-message-hover) !important; }
[class*="mentioned_"] {
    background: var(--background-mentioned) !important;
    box-shadow: inset 2px 0 0 var(--bwm-yellow) !important;
}
[class*="mentioned_"]::before { display: none !important; }
[class*="divider_"][class*="isUnread_"] { border-color: var(--bwm-red) !important; }
[class*="embedWrapper_"], [class*="codeBlock"], code, pre, [class*="attachment_"], [class*="wrapperAudio_"] {
    background: var(--bwm-bg-darker) !important;
    border: 1px solid var(--bwm-muted) !important;
}
[class*="embedWrapper_"] { border-left: 2px solid var(--bwm-accent) !important; }
blockquote [class*="blockquoteDivider"] { background: var(--bwm-accent) !important; border-radius: 0 !important; }
[class*="reaction_"] { background: var(--bwm-bg-dark) !important; border: 1px solid var(--bwm-muted) !important; }
[class*="reaction_"][class*="reactionMe_"] { border-color: var(--bwm-accent) !important; }
.mention, [class*="mention"][class*="interactive"] {
    background: var(--mention-background) !important;
    color: var(--bwm-yellow) !important;
}

/* ------------------------------------------------------------------ Caja de mensaje: un prompt */
[class*="channelTextArea_"] {
    background: var(--bwm-bg-darker) !important;
    border: 1px solid var(--bwm-muted) !important;
}
[class*="channelTextArea_"]:focus-within { border-color: var(--bwm-accent) !important; }
[class*="channelTextArea_"] [class*="scrollableContainer_"] { background: transparent !important; }
[class*="channelTextArea_"] [class*="textArea_"]::before {
    content: "❯";
    color: var(--bwm-accent);
    position: absolute;
    left: 2px;
    font-weight: 700;
}
[class*="channelTextArea_"] [class*="placeholder_"] { color: var(--bwm-fg-dim) !important; }

/* ------------------------------------------------------------------ Botones */
/* Icon buttons (user panel mic/headphones/settings, toolbars, channel header): flat, tinted on hover */
section[class*="panels_"] button, section[class*="panels_"] [role="button"],
[class*="toolbar_"] [role="button"], [class*="toolbar_"] button, [class*="iconWrapper_"],
[class*="actionButtons_"] button, [class*="buttons_"] > [class*="button_"]:not([class*="lookFilled_"]) {
    background: transparent !important;
    border: 0 !important;
    box-shadow: none !important;
}
section[class*="panels_"] button:hover, section[class*="panels_"] [role="button"]:hover,
[class*="toolbar_"] [role="button"]:hover, [class*="iconWrapper_"]:hover {
    background: color-mix(in srgb, var(--bwm-accent) 12%, transparent) !important;
}
/* Muted mic / deafened: a red glyph, no red block */
section[class*="panels_"] [class*="redIcon_"], section[class*="panels_"] [class*="strikethrough_"] {
    color: var(--bwm-red) !important;
}
section[class*="panels_"] button[class*="redIcon_"], section[class*="panels_"] [class*="buttonRed"] {
    background: color-mix(in srgb, var(--bwm-red) 14%, transparent) !important;
}

/* Text buttons in dialogs and forms: outlined in the accent, filled on hover (like a TUI button) */
[role="dialog"] button[class*="lookFilled_"][class*="colorBrand"], [class*="form_"] button[class*="lookFilled_"],
[class*="modal"] button[class*="lookFilled_"][class*="colorBrand"], button[class*="lookFilled_"][class*="colorBrand"][class*="sizeMedium"],
button[class*="lookFilled_"][class*="colorBrand"][class*="sizeLarge"] {
    background: transparent !important;
    border: 1px solid var(--bwm-accent) !important;
    color: var(--bwm-accent) !important;
}
[role="dialog"] button[class*="lookFilled_"][class*="colorBrand"]:hover, [class*="form_"] button[class*="lookFilled_"]:hover,
[class*="modal"] button[class*="lookFilled_"][class*="colorBrand"]:hover, button[class*="lookFilled_"][class*="colorBrand"][class*="sizeMedium"]:hover,
button[class*="lookFilled_"][class*="colorBrand"][class*="sizeLarge"]:hover {
    background: var(--bwm-accent) !important;
    color: var(--bwm-bg) !important;
}
button[class*="lookFilled_"][class*="colorRed"], button[class*="lookFilled_"][class*="colorDanger"] {
    background: transparent !important;
    border: 1px solid var(--bwm-red) !important;
    color: var(--bwm-red) !important;
}
button[class*="lookFilled_"][class*="colorRed"]:hover, button[class*="lookFilled_"][class*="colorDanger"]:hover {
    background: var(--bwm-red) !important;
    color: var(--bwm-bg) !important;
}
button[class*="lookFilled_"][class*="colorGreen"] { background: var(--bwm-green) !important; color: var(--bwm-bg) !important; }

/* ------------------------------------------------------------------ Campos y ventanas emergentes */
input, textarea, [class*="inputDefault_"], [class*="searchBar_"] {
    background: var(--bwm-bg-darker) !important;
    border: 1px solid var(--bwm-muted) !important;
    color: var(--bwm-fg) !important;
}
input:focus, textarea:focus, [class*="inputDefault_"]:focus-within { border-color: var(--bwm-accent) !important; }
[class*="searchBar_"] input, [class*="channelTextArea_"] textarea { border: 0 !important; background: transparent !important; }
[class*="menu_"], [class*="tooltip_"]:not([class*="tooltipPointer"]), [class*="autocomplete_"],
[class*="userPopoutOuter"], [role="dialog"][class*="root_"], [class*="quickswitcher_"] {
    background: var(--bwm-bg-dark) !important;
    border: 1px solid var(--bwm-accent) !important;
}
[class*="tooltipPointer"] { display: none !important; }
[class*="menu_"] [class*="item_"] { margin: 0 !important; }
[class*="menu_"] [class*="item_"][class*="focused_"], [class*="menu_"] [class*="item_"]:hover {
    background: var(--bwm-accent) !important;
    color: var(--bwm-bg) !important;
}
[class*="menu_"] [class*="item_"][class*="focused_"] *, [class*="menu_"] [class*="item_"]:hover * { color: var(--bwm-bg) !important; }
[class*="menu_"] [class*="colorDanger_"] { color: var(--bwm-red) !important; }
[class*="menu_"] [class*="separator_"] { background: var(--bwm-muted) !important; }
[class*="checked_"] [class*="slider_"], [class*="control_"][class*="checked_"] { background: var(--bwm-accent) !important; }

/* Barras de desplazamiento finas y cuadradas */
* { scrollbar-width: thin; scrollbar-color: var(--bwm-muted) transparent; }
::-webkit-scrollbar { width: 6px !important; height: 6px !important; }
::-webkit-scrollbar-thumb { border-radius: 0 !important; background: var(--bwm-muted) !important; border: 0 !important; }
::-webkit-scrollbar-thumb:hover { background: var(--bwm-accent) !important; }
::-webkit-scrollbar-track { background: transparent !important; border: 0 !important; }
