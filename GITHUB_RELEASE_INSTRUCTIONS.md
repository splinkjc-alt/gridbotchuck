# 🚀 GitHub Release Instructions

Step-by-step guide to create a GitHub release for GridBot Chuck.

---

## Prerequisites

- ✅ Access to the [gridbotchuck repository](https://github.com/splinkjc-alt/gridbotchuck)
- ✅ All code changes committed and pushed
- ✅ Release notes prepared (see `RELEASE_NOTES_v2.0.md`)

---

## Step 1: Navigate to Releases

1. Go to your repository: https://github.com/splinkjc-alt/gridbotchuck
2. Click on **"Releases"** in the right sidebar
3. Or directly visit: https://github.com/splinkjc-alt/gridbotchuck/releases

---

## Step 2: Create a New Release

1. Click the green button **"Create a new release"**
   - Or visit: https://github.com/splinkjc-alt/gridbotchuck/releases/new

---

## Step 3: Fill in Release Details

### Tag Version
1. Click the dropdown **"Choose a tag"**
2. Type: `v2.0.0`
3. Click **"+ Create new tag: v2.0.0 on publish"**

### Release Title
Enter:
```
GridBot Chuck v2.0 - Multi-Strategy Trading Platform
```

### Description
1. Open `RELEASE_NOTES_v2.0.md` from this repository
2. Copy the **entire content**
3. Paste it into the "Describe this release" text box

---

## Step 4: Configure Options

✅ Check **"Set as the latest release"**

Optional (recommended):
- ✅ Check **"Create a discussion for this release"** - enables community discussion

---

## Step 5: Publish

Click the green **"Publish release"** button.

---

## ✅ Verification

After publishing, verify your release:

1. Visit: https://github.com/splinkjc-alt/gridbotchuck/releases/tag/v2.0.0
2. Confirm the release notes appear correctly
3. Check that the tag `v2.0.0` is created
4. Verify download links work (Source code ZIP and TAR.GZ)

---

## 📢 Post-Release Actions

1. **Announce on social media** - Use templates from `SOCIAL_MEDIA_POSTS.md`
2. **Update README badges** - Point to latest release
3. **Monitor GitHub notifications** - Watch for issues/questions
4. **Respond to community feedback** - Engage with early adopters

---

## 🔧 Troubleshooting

### "Tag already exists"
- Choose a different version number (e.g., `v2.0.1`)
- Or delete the existing tag first (not recommended for public releases)

### Release not appearing
- Refresh the page
- Check if the release is set as a "draft" instead of published
- Verify you clicked "Publish release"

### Formatting issues in description
- Ensure Markdown syntax is correct
- Preview the description before publishing
- Use the "Preview" tab in the release editor

---

## 📋 Release Checklist

```
Before Release:
- [ ] All tests pass
- [ ] README is up to date
- [ ] RELEASE_NOTES_v2.0.md is prepared
- [ ] .env.example includes all required variables
- [ ] No sensitive data in committed files

During Release:
- [ ] Tag created: v2.0.0
- [ ] Title set correctly
- [ ] Release notes pasted
- [ ] "Set as latest release" checked
- [ ] Published

After Release:
- [ ] Release page loads correctly
- [ ] Downloads work
- [ ] Announced on social media
- [ ] Community notified
```

---

## 🎉 Congratulations!

Your release is now live! Users can:
- View release notes
- Download source code
- Star and watch the repository
- Clone and start using GridBot Chuck

---

**Need help?** Open an issue at https://github.com/splinkjc-alt/gridbotchuck/issues
