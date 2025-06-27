# UniOr PET - Translator User Guide

## Welcome to UniOr PET! 🌍

This guide will help you get started with the UniOr Post-Editing Machine Translation Tool. Whether you're new to post-editing or an experienced translator, this guide will walk you through everything you need to know.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Understanding the Interface](#understanding-the-interface)
3. [Timer Modes Explained](#timer-modes-explained)
4. [Post-Editing Workflow](#post-editing-workflow)
5. [Features and Settings](#features-and-settings)
6. [Reviewing Your Work](#reviewing-your-work)
7. [Tips for Effective Post-Editing](#tips-for-effective-post-editing)
8. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Step 1: Create Your Account

1. **Open the UniOr PET platform** in your web browser
2. **Click on the "Register" tab** if you're a new user
3. **Fill in your details:**
   - Name and Surname
   - Create a secure password (at least 8 characters)
   - Select "Translator" as your role
4. **Click "Create Account"**
5. **Switch to the Login tab** and sign in with your credentials

### Step 2: Prepare Your Files

Before starting, make sure you have:
- **Source text file**: Original text in the source language (one sentence per line)
- **Translation file**: Machine translation output (one sentence per line)

> ⚠️ **Important**: Both files must have the same number of lines!

### Step 3: Upload Your Files

1. **Upload the source text file** using the first file uploader
2. **Upload the translation file** using the second file uploader
3. The system will automatically check that both files have matching line counts

### Step 4: Choose Your Timer Mode

You'll be asked to select between two timer modes:

#### **Current Timer** (Recommended for beginners)
- Automatically tracks your editing time
- Simple and intuitive
- Time tracking happens in the background

#### **PET Timer** (Advanced)
- Manual control over timing
- You must manually start/pause the timer
- More precise for research purposes
- Requires a 2-second viewing period before you can start

---

## Understanding the Interface

### Main Editing Area

The interface adapts based on your layout preference:

#### **Vertical Layout** (Default)
- Source text appears at the top in a yellow box
- Translation to edit appears below in an editable text area
- Context segments shown above and below

#### **Horizontal Layout**
- Source text on the left side
- Translation on the right side
- Side-by-side editing experience

### Navigation Elements

- **Segment Selector**: Dropdown to jump to any segment
- **Progress Bar**: Shows your overall completion
- **Previous/Next Buttons**: Navigate between segments
- **Finish Button**: Appears on the last segment

### Sidebar Controls

- **Review All Segments**: View all your work at once
- **Save/Load**: Manage your progress
- **Layout Settings**: Switch between vertical/horizontal views
- **Context Size**: Adjust how many surrounding segments you see

---

## Timer Modes Explained

### Current Timer Mode

**How it works:**
- Timer starts automatically when you begin editing
- Tracks active editing time vs. idle time
- Idle time (30+ seconds without activity) is tracked separately
- No manual intervention required

**Best for:**
- First-time users
- Production environments
- When you want to focus purely on translation quality

### PET Timer Mode

**How it works:**
- You manually control when timing starts and stops
- Must wait 2 seconds after viewing a segment before you can start the timer
- Editing is disabled while the timer is paused
- Provides precise timing control

**Controls:**
- **⏸️ Pause Button**: Stop the timer
- **▶️ Play Button**: Start/resume the timer
- **⏳ Waiting**: Shows when you need to wait before starting

**Best for:**
- Research scenarios
- When precise timing data is critical
- Experienced post-editors

---

## Post-Editing Workflow

### Basic Workflow

1. **Start with segment 1** (or use the segment selector to jump around)
2. **Read the source text** to understand the context
3. **Review the machine translation** in the editable area
4. **Make necessary corrections:**
   - Fix grammatical errors
   - Improve word choice
   - Ensure natural flow
   - Maintain meaning accuracy
5. **Move to the next segment** using the Next button
6. **Repeat until all segments are completed**

### Navigation Tips

- **Use the segment dropdown** to jump to specific segments
- **Context segments** help you maintain consistency
- **Previous/Next buttons** save your current work automatically
- **Progress bar** shows your completion status

### What Gets Tracked

The system automatically tracks:
- **Edit time** for each segment
- **Number of insertions** (words/characters added)
- **Number of deletions** (words/characters removed)
- **Idle time** (when idle timer is enabled)

---

## Features and Settings

### Auto-Save
- **Enabled by default** - your work is saved automatically
- **Manual save** option available in the sidebar
- **Last saved time** displayed for reference

### Context Size
- **Adjust the slider** (0-5 segments) to control how much context you see
- **More context** = better consistency but more visual clutter
- **Less context** = cleaner interface but less contextual information

### Layout Options
- **Centered vs. Wide**: Choose your preferred page width
- **Vertical vs. Horizontal**: Switch editing layout style
- **Note**: Some options are disabled in PET timer mode for consistency

### Idle Timer
- **Tracks inactive time** when enabled
- **30-second threshold** - time beyond this is considered idle
- **Disabled automatically** in PET timer mode
- **Helps distinguish** between active editing and pause time

---

## Reviewing Your Work

### Review All Segments

Click **"👀 Review All Segments"** in the sidebar to:
- **See all segments** in a table format
- **Search through** your translations
- **Filter by status** (Modified/Unchanged)
- **Sort by** segment number, edit time, or number of edits
- **Jump back** to any segment for further editing

### Understanding the Statistics

After completing your work, you'll see:

#### **Time Metrics**
- **Total Time**: Overall time spent editing
- **Average Time/Segment**: Mean editing time
- **Individual segment times**: Detailed breakdown

#### **Edit Metrics**
- **Insertions**: Words/characters you added
- **Deletions**: Words/characters you removed
- **Total Edits**: Combined insertion and deletion count

#### **Quality Metrics (MTQE)**
- **BLEU Score**: Measures similarity to original (higher = fewer changes)
- **CHRF Score**: Character-level similarity measurement
- **TER Score**: Translation Error Rate (lower = fewer errors)

### Exporting Results

You can download your work in two formats:
- **CSV file**: Detailed metrics for analysis
- **JSON file**: Structured segment data with all versions

---

## Tips for Effective Post-Editing

### Before You Start
1. **Read through** a few segments to understand the content domain
2. **Check the machine translation quality** - some may need minimal editing
3. **Set your workspace** - choose comfortable layout and context settings

### During Post-Editing
1. **Focus on meaning first** - ensure the translation is accurate
2. **Then improve fluency** - make it sound natural in the target language
3. **Be consistent** - use the context to maintain terminology and style
4. **Don't over-edit** - if the meaning is clear, minimal changes may be sufficient
5. **Take breaks** - the idle timer will track when you're not actively editing

### Quality Guidelines
- **Preserve the source meaning** above all else
- **Maintain appropriate register** and tone
- **Fix grammatical errors** and awkward phrasing
- **Ensure terminological consistency** across segments
- **Consider target audience** and cultural adaptation when necessary

### Time Management
- **Don't rush** - quality is more important than speed
- **Use context** to avoid inconsistencies that waste time later
- **Take notes** if you notice recurring issues or terminology
- **Save regularly** if auto-save is disabled

---

## Troubleshooting

### Common Issues

#### **"No editing time was recorded"**
- **Cause**: You moved to the next segment too quickly
- **Solution**: In PET mode, wait for the 2-second minimum viewing time before starting the timer
- **Prevention**: Always start the timer before making edits in PET mode

#### **Files won't upload**
- **Check file format**: Only .txt files are supported
- **Check line counts**: Both files must have exactly the same number of lines
- **Check encoding**: Ensure files are UTF-8 encoded

#### **Can't edit the text area**
- **PET timer mode**: Make sure the timer is started (▶️ button)
- **Check if paused**: Look for the pause indicator in the interface

#### **Lost work**
- **Check auto-save**: Your work should be automatically saved
- **Use the Load button**: Click "📂 Load" in the sidebar to restore previous work
- **Check login status**: Make sure you're logged in with the correct account

### Getting Help

If you encounter issues:
1. **Check this guide** for common solutions
2. **Try refreshing** the page (your work should be saved)
3. **Contact support** at antonio.castaldo@phd.unipi.it
4. **Include details**: What you were doing when the issue occurred

### Browser Compatibility

For the best experience:
- **Use a modern browser** (Chrome, Firefox, Safari, Edge)
- **Enable JavaScript** - required for timer functionality
- **Clear cache** if you experience unusual behavior
- **Stable internet connection** recommended for auto-save

---

## Best Practices Summary

✅ **Do:**
- Read the source text carefully before editing
- Use context segments to maintain consistency
- Focus on accuracy first, then fluency
- Take advantage of auto-save functionality
- Review your work using the Review All Segments feature

❌ **Don't:**
- Rush through segments without proper review
- Make unnecessary changes if the translation is adequate
- Ignore the context provided by surrounding segments
- Forget to start the timer in PET mode
- Copy-paste text (manual typing is required for accurate metrics)

---

## Need More Help?

- **Technical Issues**: antonio.castaldo@phd.unipi.it
- **Project Website**: [www.ancastal.com](https://www.ancastal.com)
- **Tool Documentation**: Available in the platform interface

**Happy post-editing!** 🚀

---

*This guide covers the essential features for translators. For advanced features or project management capabilities, please refer to the administrator documentation or contact support.*
