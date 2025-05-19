# Typhon - Performance Testing Assistant

Typhon is an AI-powered performance testing tool that generates JMeter test plans using Google's Gemini AI. It simplifies the creation of performance tests by providing intelligent suggestions and configurations.

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

Run the performance test assistant:
```bash
python performance_test_assistant.py
```

The interactive assistant will guide you through:
1. Providing your performance testing requirements
2. Receiving AI-generated test setup suggestions
3. Refining the setup based on your feedback
4. Generating a JMeter test plan (.jmx file)

All generated test plans are saved in the `jmeter-tests/test-plans` directory.

## Features

- **Interactive Test Design**: Conversational interface to describe your testing needs
- **Gemini 2.0 Flash AI**: Advanced AI model for intelligent test configuration
- **Multiple Test Types**: Support for load, stress, spike, endurance, and scalability tests
- **Customizable Parameters**: Easily adjust users, ramp-up time, duration, and more
- **JMeter Integration**: Generate ready-to-use JMeter test plans
- **Test Refinement**: Iterative process to fine-tune your test setup
- **Compatibility Checks**: Ensures generated plans work with JMeter 5.6.3
- **Organized Test Management**: Structured storage of test plans and reports

## Project Structure

- `performance_test_assistant.py`: Main script with the PerformanceTestAssistant class
- `jmeter-tests/`: Directory containing generated test plans and data
- `requirements.txt`: List of Python dependencies

## Future Plans

- Web interface for easier interaction with the assistant
- Support for more performance testing tools beyond JMeter
- Test result analysis and visualization
- Integration with CI/CD pipelines
- Extended templates for various application types (REST APIs, databases, etc.)
- Load test distribution capabilities
- Performance test scheduling
- Historical test results comparison

## License

This project is licensed under the MIT License - see the LICENSE file for details. 