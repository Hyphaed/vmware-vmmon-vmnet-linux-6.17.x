# GitHub Analytics Guide

This document explains how to track downloads, views, and other metrics for your GitHub repository.

## 📊 Current Repository Statistics

**Repository**: Hyphaed/vmware-vmmon-vmnet-linux-6.17.x

- ⭐ **Stars**: 2
- 👁️ **Watchers**: 2
- 🔀 **Forks**: 0
- 🐛 **Open Issues**: 0 (2 closed)
- 📏 **Size**: 40 KB
- 💻 **Language**: Shell
- 📅 **Created**: October 6, 2025
- 🔄 **Last Updated**: October 9, 2025

---

## 🎯 Where to Find Download & Clone Statistics

### Method 1: GitHub Insights Tab (Owner Access Required)

As the repository owner, you have access to detailed traffic analytics:

1. **Go to your repository**: https://github.com/Hyphaed/vmware-vmmon-vmnet-linux-6.17.x/

2. **Click "Insights"** tab (top navigation bar)

3. **Navigate to specific sections**:

#### 📈 Traffic (Most Important for Downloads)
**URL**: https://github.com/Hyphaed/vmware-vmmon-vmnet-linux-6.17.x/graphs/traffic

Shows **last 14 days** of data:
- **Git clones**: 
  - Total clones (how many times repo was cloned)
  - Unique cloners (number of unique users)
  - Graph showing daily trend
- **Visitors**:
  - Total views (page views)
  - Unique visitors (unique users visiting)
  - Daily breakdown

**Example view**:
```
Git clones
  15 clones    8 unique cloners
  
Visitors
  124 views    45 unique visitors
```

#### ⭐ Stars
**URL**: https://github.com/Hyphaed/vmware-vmmon-vmnet-linux-6.17.x/stargazers

- See who starred your repository
- Timeline of when stars were added
- Total star count

#### 🔀 Forks
**URL**: https://github.com/Hyphaed/vmware-vmmon-vmnet-linux-6.17.x/network/members

- List of all forks
- Who forked your repository
- When they forked it

#### 👥 Contributors
**URL**: https://github.com/Hyphaed/vmware-vmmon-vmnet-linux-6.17.x/graphs/contributors

- Who contributed code
- Number of commits per contributor
- Lines added/removed

#### 📦 Dependency Graph
**URL**: https://github.com/Hyphaed/vmware-vmmon-vmnet-linux-6.17.x/network/dependents

- Projects that depend on your repository
- Useful if you publish packages

---

## 📥 Understanding "Downloads"

GitHub doesn't track direct "downloads" like a traditional download counter because:

1. **Git Clone**: Users clone the repository (tracked in Traffic → Git clones)
2. **Download ZIP**: Users download as ZIP file (counted as a page view)
3. **Release Assets**: Downloads of release files (tracked per release)

### What Counts as a "Download":

1. **Git Clones** (most accurate):
   ```bash
   git clone https://github.com/Hyphaed/vmware-vmmon-vmnet-linux-6.17.x.git
   ```
   ✅ Tracked in Traffic → Git clones

2. **Download ZIP** button:
   - Click "Code" → "Download ZIP"
   - ⚠️ Only tracked as a page view, not separately counted

3. **Release Downloads** (if you create releases):
   - Each release asset download is tracked individually
   - Most reliable download metric

---

## 🎯 How to Create Releases for Better Download Tracking

To track downloads more accurately, create releases:

### Step 1: Create a Release

1. Go to: https://github.com/Hyphaed/vmware-vmmon-vmnet-linux-6.17.x/releases

2. Click **"Create a new release"** or **"Draft a new release"**

3. Fill in release information:
   ```
   Tag version: v1.1.0
   Release title: Version 1.1.0 - Fix Issues #2 and #3
   Description:
   - Fixed hardcoded log file path
   - Added automatic objtool detection for kernel 6.16.3+
   - Improved compatibility with Pop!_OS and Ubuntu
   ```

4. **Attach files** (optional):
   - Upload `.tar.gz` or `.zip` archives
   - Each file download will be tracked separately

5. Click **"Publish release"**

### Step 2: View Release Download Statistics

Once you have releases, you can see downloads:

1. Go to: https://github.com/Hyphaed/vmware-vmmon-vmnet-linux-6.17.x/releases

2. Each release shows download counts for attached files:
   ```
   vmware-modules-6.17.x.tar.gz    ⬇️ 47 downloads
   vmware-modules-6.16.x.tar.gz    ⬇️ 23 downloads
   ```

---

## 📊 Using GitHub API for Statistics

You can programmatically fetch statistics using the GitHub API:

### Get Basic Repository Info

```bash
curl -s "https://api.github.com/repos/Hyphaed/vmware-vmmon-vmnet-linux-6.17.x"
```

Returns:
- Stars count
- Forks count
- Watchers count
- Open issues
- Size
- Creation date

### Get Release Download Counts

```bash
curl -s "https://api.github.com/repos/Hyphaed/vmware-vmmon-vmnet-linux-6.17.x/releases"
```

Returns download counts for each release asset.

### Get Clone Traffic (Owner Only - Requires Token)

```bash
curl -H "Authorization: token YOUR_GITHUB_TOKEN" \
  "https://api.github.com/repos/Hyphaed/vmware-vmmon-vmnet-linux-6.17.x/traffic/clones"
```

Returns:
- Total clones
- Unique cloners
- Daily breakdown (last 14 days)

---

## 🔧 Third-Party Analytics Tools

For more advanced analytics, consider:

### 1. **GitHub Badges** (Show stats in README)

Add to your README.md:

```markdown
![GitHub stars](https://img.shields.io/github/stars/Hyphaed/vmware-vmmon-vmnet-linux-6.17.x?style=social)
![GitHub forks](https://img.shields.io/github/forks/Hyphaed/vmware-vmmon-vmnet-linux-6.17.x?style=social)
![GitHub watchers](https://img.shields.io/github/watchers/Hyphaed/vmware-vmmon-vmnet-linux-6.17.x?style=social)
![GitHub repo size](https://img.shields.io/github/repo-size/Hyphaed/vmware-vmmon-vmnet-linux-6.17.x)
![GitHub downloads](https://img.shields.io/github/downloads/Hyphaed/vmware-vmmon-vmnet-linux-6.17.x/total)
```

### 2. **Shields.io**

Website: https://shields.io/

Custom badges for:
- Download counts
- Stars
- Forks
- Issues
- License

### 3. **GitHub Traffic Analytics Tools**

- **Somsubhra/github-traffic-stats**: Store historical traffic data
- **nchah/github-traffic-cli**: CLI tool for traffic stats
- **gayanvoice/github-profile-views-counter**: Track profile views

---

## 📈 Best Practices for Tracking Downloads

1. **Create releases regularly**:
   - Tag important versions
   - Attach downloadable assets
   - This gives the most accurate download counts

2. **Check Traffic weekly**:
   - Traffic data only shows last 14 days
   - Export/save data regularly if you want historical records

3. **Monitor clone activity**:
   - Clones indicate active usage
   - More reliable than page views

4. **Engage with users**:
   - Stars and forks show interest
   - Issues and discussions show active usage
   - Contributors show community engagement

5. **Use analytics to improve**:
   - High views but low clones? Improve documentation
   - Many clones but issues? Improve code quality
   - Lots of stars? Consider adding more features

---

## 🎯 Quick Access Links for Your Repository

**Main Analytics Dashboard**:
- Traffic: https://github.com/Hyphaed/vmware-vmmon-vmnet-linux-6.17.x/graphs/traffic
- Stars: https://github.com/Hyphaed/vmware-vmmon-vmnet-linux-6.17.x/stargazers
- Forks: https://github.com/Hyphaed/vmware-vmmon-vmnet-linux-6.17.x/network/members
- Contributors: https://github.com/Hyphaed/vmware-vmmon-vmnet-linux-6.17.x/graphs/contributors
- All Insights: https://github.com/Hyphaed/vmware-vmmon-vmnet-linux-6.17.x/pulse

**Issue Tracking**:
- Open Issues: https://github.com/Hyphaed/vmware-vmmon-vmnet-linux-6.17.x/issues
- Closed Issues: https://github.com/Hyphaed/vmware-vmmon-vmnet-linux-6.17.x/issues?q=is%3Aissue+is%3Aclosed

**Releases**:
- All Releases: https://github.com/Hyphaed/vmware-vmmon-vmnet-linux-6.17.x/releases
- Create Release: https://github.com/Hyphaed/vmware-vmmon-vmnet-linux-6.17.x/releases/new

---

## 📝 Summary

| Metric | Where to Find | Accuracy |
|--------|--------------|----------|
| Git Clones | Insights → Traffic | ✅ High |
| Page Views | Insights → Traffic | ✅ High |
| Stars | Insights → Stars | ✅ Perfect |
| Forks | Insights → Forks | ✅ Perfect |
| Release Downloads | Releases page | ✅ Perfect |
| ZIP Downloads | Not tracked separately | ❌ No data |
| Script Usage | Not tracked | ❌ No data |

**Recommendation**: Create releases with downloadable assets to get the most accurate download statistics.

---

**Last Updated**: October 9, 2025

