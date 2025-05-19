# Performance Testing Script Generator

This project provides an interactive tool to generate performance test setups and JMeter test plans using Google's Gemini AI.

## Prerequisites

- Python 3.7 or higher
- Google Gemini API key
- JMeter installed (for running the generated test plans)

## Installation

1. Clone this repository
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project root and add your Google Gemini API key:
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```

## Usage

The project consists of two main scripts:

### 1. Performance Test Setup Generator (`performance_test_setup.py`)

This script helps you create a detailed performance test setup:

1. Run the script:
   ```bash
   python performance_test_setup.py
   ```
2. Follow the interactive prompts to:
   - Select the type of performance test (Load, Stress, Spike, Endurance, or Scalability)
   - Enter test parameters (target URL, concurrent users, ramp-up time, test duration)
   - Review and modify the generated test setup
3. The script will save your test setup to `test_setup.json`

### 2. JMeter Test Plan Generator (`jmeter_generator.py`)

This script generates a JMeter test plan based on your test setup:

1. Run the script:
   ```bash
   python jmeter_generator.py
   ```
2. The script will:
   - Load your test setup from `test_setup.json`
   - Generate a JMeter test plan using Gemini AI
   - Save the test plan as a .jmx file in the `jmeter-tests` directory

## Generated Files

- `test_setup.json`: Contains your performance test configuration
- `jmeter-tests/*.jmx`: Generated JMeter test plans

## Features

- Interactive test setup generation
- Support for multiple types of performance tests
- AI-powered test plan generation
- Customizable test parameters
- JMeter-compatible output

## Notes

- Make sure to review the generated JMeter test plans before running them
- The Gemini AI may occasionally need adjustments to the generated test plans
- Test parameters should be chosen carefully based on your system's capabilities

## License

This project is licensed under the MIT License - see the LICENSE file for details. 