# UniOr PET: An Online Platform for Translation Post-Editing

[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/streamlit-1.46.0-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Overview

UniOr PET (University of Oriental Studies Post-Editing Tool) is a web-based platform designed for translation post-editing research and practice. The tool provides comprehensive metrics collection, time tracking, and user-friendly interfaces for improving machine translation outputs through human post-editing.

## Features

### Core Functionality
- **Segment-by-segment post-editing**: Edit translations with contextual information
- **Multiple timer modes**: 
  - Current Timer: Automatic time tracking during editing
  - PET Timer: Manual control with pause/resume functionality
- **Real-time metrics**: Track insertions, deletions, and editing time
- **Progress persistence**: Save and resume work across sessions
- **Multi-user support**: Authentication and user-specific data management

### Advanced Features
- **Idle time detection**: Separate tracking of active vs. idle editing time
- **Context visualization**: Configurable context window for surrounding segments
- **Horizontal/vertical layouts**: Flexible editing interface options
- **Review functionality**: Comprehensive overview of all edited segments
- **Export capabilities**: Download results in CSV and JSON formats
- **MTQE scoring**: Automatic calculation of BLEU, CHRF, and TER metrics

### Technical Features
- **MongoDB integration**: Secure cloud-based data storage
- **Auto-save functionality**: Automatic progress preservation
- **Responsive design**: Mobile and desktop compatibility
- **Real-time collaboration**: Multi-user project management capabilities

## Installation

### Prerequisites
- Python 3.8 or higher
- MongoDB instance (local or cloud-based)
- pip package manager

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/unior-pet.git
   cd unior-pet
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   Create a `.streamlit/secrets.toml` file:
   ```toml
   MONGO_CONNECTION_STRING = "your_mongodb_connection_string"
   VERSION = "1.0.0"
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

## Usage

### Getting Started

1. **Authentication**: Register a new account or login with existing credentials
2. **File Upload**: Upload source and translation files (one sentence per line)
3. **Timer Mode Selection**: Choose between Current Timer or PET Timer modes
4. **Post-Editing**: Edit translations segment by segment with real-time feedback
5. **Review and Export**: Review all edits and download results

### Input Format

The tool expects two text files:
- **Source file**: Original text, one sentence per line
- **Translation file**: Machine translation output, one sentence per line

Both files must have the same number of lines.

### Output Formats

- **CSV**: Detailed metrics including edit times, insertions, deletions
- **JSON**: Structured data with source, original, and post-edited segments
- **Database**: Persistent storage in MongoDB for session management

## Research Applications

UniOr PET is designed to support various research scenarios:

### Translation Quality Assessment
- Measure post-editing effort through time and edit distance metrics
- Compare different machine translation systems
- Analyze translator behavior patterns

### User Studies
- Controlled experiments with different interface configurations
- Comparative studies between timer modes
- Analysis of cognitive load through idle time tracking

### Productivity Analysis
- Measure translation productivity improvements
- Identify segments requiring most editing effort
- Track learning curves over multiple sessions

## Metrics and Evaluation

### Collected Metrics
- **Temporal metrics**: Editing time, idle time, pause duration
- **Edit distance metrics**: Character/word insertions and deletions
- **Quality metrics**: BLEU, CHRF, TER scores
- **Behavioral metrics**: Pause patterns, segment navigation

### Statistical Analysis
The tool provides built-in statistical analysis including:
- Average editing time per segment
- Distribution of edit operations
- Quality improvement measurements
- Productivity trends over time

## Architecture

### Frontend
- **Streamlit**: Web application framework
- **Custom CSS**: Responsive design and user experience
- **JavaScript integration**: Real-time interactions and timer management

### Backend
- **Python**: Core application logic
- **MongoDB**: Data persistence and user management
- **AsyncIO**: Asynchronous database operations

### Data Models
- **EditingSession**: Tracks timing and activity data
- **EditMetrics**: Stores post-editing measurements
- **TimeTracker**: Manages different timer modes and calculations

## Citation

If you use UniOr PET in your research, please cite:

```bibtex
@inproceedings{castaldo_2025_UniOrPET,
    address = {Geneva, Switzerland},
    title = {UniOr {PET}: {An} {Online} {Platform} for {Translation} {Post-Editing}},
    url = {https://mtsummit2025.unige.ch/},
    booktitle = {20th Machine Translation Summit: {Products and Projects track}},
    publisher = {European Association for Machine Translation},
    author = {Castaldo, Antonio and Sheila Castilho and Joss Moorkens and Johanna Monti},
    editor = {Esplà-Gomis, Miquel and Vincent Vandeghinste},
    month = june,
    year = {2025},
}
```

## Contributing

We welcome contributions from the research community. Please see our contributing guidelines for:
- Bug reports and feature requests
- Code contributions and pull requests
- Documentation improvements
- Research collaboration opportunities

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

- **Antonio Castaldo** - antonio.castaldo@phd.unipi.it
- **Project Page**: [https://www.ancastal.com](https://www.ancastal.com)
- **Conference Presentation**: [MT Summit 2025](https://mtsummit2025.unige.ch/)

## Acknowledgments

This research was conducted at the University of Pisa in collaboration with Dublin City University. We thank the European Association for Machine Translation for supporting this work through the MT Summit 2025 conference.

---

*For technical support, research collaboration, or questions about the platform, please contact the development team.*
