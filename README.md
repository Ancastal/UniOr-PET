# UniOr Post-Editing Tool 🌍

A streamlined web application for machine translation post-editing tasks, developed by Antonio Castaldo, PhD candidate in Artificial Intelligence at the University of Pisa.

## Features ✨

- **User Authentication**: Secure login system to track individual progress
- **Real-time Editing**: Intuitive interface for post-editing machine translations
- **Progress Tracking**: Automatic saving and loading of editing progress
- **Dual Timer Modes**:
  - Current Timer: Automatic time tracking
  - PET Timer: Manual control with pause/resume functionality
- **Context Visualization**: View surrounding segments for better context
- **Layout Options**: Choose between centered or wide layout
- **Visual Feedback**: Real-time highlighting of edits and changes
- **Detailed Statistics**: Track editing time, insertions, and deletions
- **Export Options**: Download metrics and edited segments in CSV/JSON formats

## Getting Started 🚀

### Prerequisites

- Python 3.7+
- MongoDB database
- Streamlit

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/unior-pet.git
cd unior-pet
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure MongoDB:
   - Create a `.streamlit/secrets.toml` file with your MongoDB connection string:
   ```toml
   MONGO_CONNECTION_STRING = "your_mongodb_connection_string"
   VERSION = "1.0.0"
   ```

4. Run the application:
```bash
streamlit run app.py
```

## Usage 📝

1. **Login/Register**: Create an account or log in to start editing
2. **Upload Files**: 
   - Source text file (one sentence per line)
   - Translation file (one sentence per line)
3. **Choose Timer Mode**:
   - Current Timer: Automatic tracking
   - PET Timer: Manual control
4. **Edit Segments**:
   - View source and translation side by side
   - Edit translations with context
   - Track changes in real-time
5. **Monitor Progress**:
   - View editing statistics
   - Track time spent and changes made
6. **Export Results**:
   - Download metrics as CSV
   - Export edited segments as JSON

## Features in Detail 🔍

### Timer Modes
- **Current Timer**: Automatically tracks editing time
- **PET Timer**: Allows manual control with pause/resume functionality

### Layout Options
- **Centered**: Focused editing experience
- **Wide**: Maximized screen space utilization
- **Horizontal View**: Side-by-side source and translation display

### Statistics Tracking
- Editing time per segment
- Idle time tracking
- Word insertions and deletions
- Overall progress metrics

### Auto-save Features
- Automatic progress saving
- Resume work from last edited segment
- Secure cloud backup

## Contributing 🤝

Contributions are welcome! Please feel free to submit a Pull Request.

## Contact 📧

Antonio Castaldo - [antonio.castaldo@phd.unipi.it](mailto:antonio.castaldo@phd.unipi.it)

Website: [www.ancastal.com](https://www.ancastal.com)

## License 📄

This project is licensed under the MIT License - see the LICENSE file for details.
