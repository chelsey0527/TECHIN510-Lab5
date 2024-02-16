# Seattle Events Interactive Data Visualization App

## Overview

This project provides an interactive platform for exploring and visualizing data related to events in Seattle, utilizing a custom dataset generated from web scraping. The application offers insights into event categories, locations, dates, and weather conditions, enabling users to filter and analyze Seattle's event landscape effectively.

## Project Structure

- `scraper.py`: Script for scraping event and weather data from [Visit Seattle](https://visitseattle.org/events/) and weather APIs, storing the data in a PostgreSQL database hosted on Azure.
- `app.py`: Streamlit application for data visualization, allowing users to interact with the dataset through various charts and filters.
- `db.py`: Contains utility functions for database connection.
- `data/`: Directory for storing JSON files with scraped links and event data.

## Setup and Installation

**Environment Setup**: Ensure Python 3.8+ is installed. Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
pip install -r requirements.txt

## Reflection
Throughout the Seattle Events Interactive Data Visualization App project, I've evolved significantly. It taught me the complexities of web scraping, the power of data visualization with Streamlit, and efficient database management. This journey has not only honed my technical skills but also deepened my understanding of making data accessible and engaging for a broad audience.
