#include "appName.hpp"

#include <algorithm>
#include <chrono>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace fs = std::filesystem;

namespace {
  struct SEntry {
    std::string id, name, wmClass;
  };

  std::vector<SEntry>                          g_entries;
  std::unordered_map<std::string, std::string> g_resolved;
  std::vector<fs::file_time_type>              g_stamps;
  std::chrono::steady_clock::time_point        g_lastCheck;
  bool                                         g_loaded = false;

  std::vector<fs::path> applicationDirs() {
    std::vector<fs::path> dirs;

    const char* dataHome = std::getenv("XDG_DATA_HOME");
    const char* home     = std::getenv("HOME");
    if (dataHome && *dataHome)
      dirs.emplace_back(fs::path(dataHome) / "applications");
    else if (home && *home)
      dirs.emplace_back(fs::path(home) / ".local/share/applications");

    const char*       dataDirs = std::getenv("XDG_DATA_DIRS");
    const std::string list     = dataDirs && *dataDirs ? dataDirs : "/usr/local/share:/usr/share";
    size_t            start    = 0;
    while (start <= list.size()) {
      size_t end = list.find(':', start);
      if (end == std::string::npos)
        end = list.size();
      if (end > start)
        dirs.emplace_back(fs::path(list.substr(start, end - start)) / "applications");
      start = end + 1;
    }

    return dirs;
  }

  // Directory times move when an entry is added, removed or renamed, which is how
  // an installed web app reaches this cache without a Hyprland reload.
  std::vector<fs::file_time_type> stamps(const std::vector<fs::path>& dirs) {
    std::vector<fs::file_time_type> result;
    for (const auto& dir : dirs) {
      std::error_code ec;
      const auto      time = fs::last_write_time(dir, ec);
      result.push_back(ec ? fs::file_time_type::min() : time);
    }
    return result;
  }

  SEntry readEntry(const fs::path& path) {
    SEntry        entry{.id = path.stem().string()};
    std::ifstream file(path);
    std::string   line;
    bool          inEntry = false;

    while (std::getline(file, line)) {
      if (line.starts_with('[')) {
        inEntry = line == "[Desktop Entry]";
        continue;
      }
      if (!inEntry)
        continue;
      if (line.starts_with("Name="))
        entry.name = line.substr(5);
      else if (line.starts_with("StartupWMClass="))
        entry.wmClass = line.substr(15);
    }

    return entry;
  }

  void load(const std::vector<fs::path>& dirs) {
    g_entries.clear();
    g_resolved.clear();

    // Earlier directories win, so a user's own entry overrides the system one.
    std::unordered_set<std::string> seen;
    for (const auto& dir : dirs) {
      std::error_code ec;
      for (const auto& file : fs::directory_iterator(dir, ec)) {
        if (file.path().extension() != ".desktop" || !seen.insert(file.path().filename().string()).second)
          continue;
        auto entry = readEntry(file.path());
        if (!entry.name.empty())
          g_entries.push_back(std::move(entry));
      }
    }
  }

  std::string lower(std::string text) {
    std::ranges::transform(text, text.begin(), [](unsigned char c) { return std::tolower(c); });
    return text;
  }
}

std::string omarchyAppName(const std::string& windowClass) {
  if (windowClass.empty())
    return "";

  const auto now = std::chrono::steady_clock::now();
  if (!g_loaded || now - g_lastCheck > std::chrono::seconds(2)) {
    g_lastCheck      = now;
    const auto dirs  = applicationDirs();
    auto       times = stamps(dirs);
    if (!g_loaded || times != g_stamps) {
      load(dirs);
      g_stamps = std::move(times);
      g_loaded = true;
    }
  }

  if (const auto cached = g_resolved.find(windowClass); cached != g_resolved.end())
    return cached->second;

  std::string name;
  for (const auto& entry : g_entries) {
    if (entry.wmClass == windowClass) {
      name = entry.name;
      break;
    }
  }
  if (name.empty()) {
    const auto wanted = lower(windowClass);
    for (const auto& entry : g_entries) {
      if (lower(entry.id) == wanted) {
        name = entry.name;
        break;
      }
    }
  }

  g_resolved[windowClass] = name;
  return name;
}
