std = "lua51"

read_globals = {
    "LOC",
    "_PLUGIN",
    "import",
}

exclude_files = {
    ".tmp/**",
    "artifacts/**",
    "types/**",
    "vendor/**",
    "**/vendor/**",
    "lightroom/FGA Diagnostics.lrdevplugin/dkjson.lua",
}

codes = true
ranges = true
max_line_length = 120
max_comment_line_length = 120
max_string_line_length = 120
