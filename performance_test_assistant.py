import os
import google.generativeai as genai
from dotenv import load_dotenv
import json
from datetime import datetime
import re

# Load environment variables
load_dotenv()

# Configure Gemini API
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

class PerformanceTestAssistant:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.conversation_history = []
        
    def _get_system_prompt(self):
        return """You are a performance testing expert assistant. Your role is to:
        1. Analyze user requirements for performance testing
        2. Suggest optimal test configurations including:
           - Number of users/threads
           - Ramp-up period
           - Test duration
           - Think time
        3. Help refine the setup based on user feedback
        4. Generate JMeter test plan configurations in .jmx format
        
        Always provide clear, detailed explanations for your suggestions."""

    def get_test_setup_suggestion(self, user_input):
        """Generate test setup suggestion based on user's requirements"""
        prompt = f"""As a JMeter expert, analyze this test requirement and create a practical test plan: {user_input}

        1. You must determine the appropriate test type (load, stress, spike, etc.) based on the requirement
        2. Identify the SPECIFIC test parameters relevant to this particular test type
        3. Provide EXACT values for each parameter (use concrete numbers, not ranges)
        4. Determine what specific information is needed from the user for this test
        
        FORMAT YOUR RESPONSE LIKE THIS (plain text, no markdown):
        
        TEST TYPE: [brief name and one-line description]
        
        TEST PARAMETERS:
        - Users/Threads: [number]
        - Ramp-up Period: [seconds]
        - Duration: [time]
        [Add other relevant parameters with specific values]
        
        REQUIRED INFORMATION:
        - [Item 1]: [brief description]
        - [Item 2]: [brief description]
        [List any information you need from the user]
        
        Important:
        - Format must be clean and easy to read in a terminal
        - No markdown formatting (no *, **, etc.)
        - No explanatory text, just the sections above
        - Be concise but informative
        - Use plain text formatting only
        - Give specific values, not ranges"""
        
        response = self.model.generate_content(prompt)
        self.conversation_history.append({"role": "user", "content": user_input})
        self.conversation_history.append({"role": "assistant", "content": response.text})
        
        return response.text

    def refine_setup(self, feedback):
        """Refine the test setup based on user feedback"""
        
        # Collect the conversation history to provide context
        conversation = []
        for message in self.conversation_history:
            if message["role"] == "user":
                conversation.append(f"User: {message['content']}")
            else:
                conversation.append(f"Assistant: {message['content']}")
        
        conversation_text = "\n".join(conversation)
        
        prompt = f"""Previous conversation:
{conversation_text}

User feedback: {feedback}

As a JMeter expert, update the test plan based on this feedback.

FORMAT YOUR RESPONSE LIKE THIS (plain text, no markdown):

TEST TYPE: [same as before unless changed by feedback]

TEST PARAMETERS:
- Users/Threads: [number]
- Ramp-up Period: [seconds]
- Duration: [time]
[Include all parameters with updated values based on feedback]

REQUIRED INFORMATION:
- [Item 1]: [description]
- [Item 2]: [description]
[List any information still needed from the user]

Important:
- Format must be clean and easy to read in a terminal
- No markdown formatting (no *, **, etc.)
- No explanatory text
- Keep all unchanged parameters from the previous setup
- Update only the parameters mentioned in the feedback
- Use plain text formatting only"""
        
        response = self.model.generate_content(prompt)
        self.conversation_history.append({"role": "user", "content": feedback})
        self.conversation_history.append({"role": "assistant", "content": response.text})
        
        return response.text

    def generate_jmx(self, final_setup):
        """Generate complete JMeter test plan based on the final setup"""
        # Collect the conversation history to provide context
        conversation = []
        for message in self.conversation_history:
            if message["role"] == "user":
                conversation.append(f"User: {message['content']}")
            else:
                conversation.append(f"Assistant: {message['content']}")
        
        conversation_text = "\n".join(conversation)
        
        prompt = f"""Conversation history:
{conversation_text}

Final test setup:
{final_setup}

As a JMeter expert, create a complete JMeter test plan in XML format based on this setup.

Requirements:
1. Create a JMX file compatible with JMeter 5.6.3
2. Include ALL components necessary for the specific test type mentioned
3. Use the full range of standard JMeter 5.6.3 components as appropriate
4. Choose the most suitable components based on the test requirements
5. Extract ALL parameters from the final setup and use them in the test plan
6. Return ONLY the XML content with no explanations

Important compatibility notes:
- Avoid these known incompatible elements: ResponseTimeAssertion, BSFSampler, BSFPreProcessor, BSFPostProcessor
- DO NOT include these problematic fields in SampleSaveConfiguration: sampleCounts, errorCount, hostname, sampleCount
- If domain is not specified, use example.com as the default
- Leverage all appropriate JMeter features based on the test type (load, stress, spike, etc.)
- Use JMeter's built-in capabilities for the specific test scenario (database, API, web, etc.)"""
        
        response = self.model.generate_content(prompt)
        
        # Clean up the XML content
        jmx_content = self._clean_jmx_content(response.text)
        
        # Remove any problematic fields from SampleSaveConfiguration
        jmx_content = self._fix_sample_save_configuration(jmx_content)
        
        # Remove any incompatible JMeter elements
        jmx_content = self._validate_jmeter_compatibility(jmx_content)
        
        # If the JMX is empty or invalid, use default template
        if not self._is_valid_xml(jmx_content):
            jmx_content = self._create_default_jmx()
            
        return jmx_content
    
    def _clean_jmx_content(self, content):
        """Clean up the JMX content to ensure it's valid XML"""
        # Remove markdown code block markers if present
        content = re.sub(r'```xml|```jmx|```', '', content)
        
        # Extract the XML content - start with XML declaration or root element
        xml_pattern = re.compile(r'(<\?xml.*?>\s*)?<jmeterTestPlan.*?</jmeterTestPlan>', re.DOTALL)
        match = xml_pattern.search(content)
        
        if match:
            xml_content = match.group(0)
        else:
            # If no match, try to find any XML-like content
            xml_content = re.search(r'<[^>]+>.*</[^>]+>', content, re.DOTALL)
            if xml_content:
                xml_content = xml_content.group(0)
            else:
                # If still no match, return original content with warning
                return '<?xml version="1.0" encoding="UTF-8"?>\n<!-- WARNING: Could not extract valid XML -->\n' + content
        
        # Ensure it starts with an XML declaration
        if not xml_content.startswith('<?xml'):
            xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_content
            
        return xml_content
    
    def _fix_sample_save_configuration(self, xml_content):
        """Remove problematic fields from SampleSaveConfiguration"""
        # List of problematic fields
        problematic_fields = [
            'sampleCounts',
            'errorCount',
            'assertions',
            'hostname',
            'threadCounts',
            'sampleCount'
        ]
        
        for field in problematic_fields:
            # Remove lines containing these fields in SampleSaveConfiguration
            pattern = re.compile(f'<{field}>.*?</{field}>', re.DOTALL)
            xml_content = pattern.sub('', xml_content)
        
        return xml_content
    
    def _is_valid_xml(self, xml_content):
        """Check if the XML content is valid JMeter XML"""
        required_elements = [
            '<jmeterTestPlan',
            '<hashTree>',
            '<ThreadGroup',
            'num_threads',
            'ramp_time'
        ]
        
        for element in required_elements:
            if element not in xml_content:
                return False
        
        return True
    
    def _create_default_jmx(self):
        """Create a default JMX template as fallback"""
        return """<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.6.3">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="Performance Test Plan" enabled="true">
      <stringProp name="TestPlan.comments"></stringProp>
      <boolProp name="TestPlan.functional_mode">false</boolProp>
      <boolProp name="TestPlan.tearDown_on_shutdown">true</boolProp>
      <boolProp name="TestPlan.serialize_threadgroups">false</boolProp>
      <elementProp name="TestPlan.user_defined_variables" elementType="Arguments" guiclass="ArgumentsPanel" testclass="Arguments" testname="User Defined Variables" enabled="true">
        <collectionProp name="Arguments.arguments"/>
      </elementProp>
      <stringProp name="TestPlan.user_define_classpath"></stringProp>
    </TestPlan>
    <hashTree>
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="Thread Group" enabled="true">
        <stringProp name="ThreadGroup.on_sample_error">continue</stringProp>
        <elementProp name="ThreadGroup.main_controller" elementType="LoopController" guiclass="LoopControlPanel" testclass="LoopController" testname="Loop Controller" enabled="true">
          <boolProp name="LoopController.continue_forever">false</boolProp>
          <stringProp name="LoopController.loops">1</stringProp>
        </elementProp>
        <stringProp name="ThreadGroup.num_threads">100</stringProp>
        <stringProp name="ThreadGroup.ramp_time">30</stringProp>
        <boolProp name="ThreadGroup.scheduler">true</boolProp>
        <stringProp name="ThreadGroup.duration">300</stringProp>
        <stringProp name="ThreadGroup.delay"></stringProp>
        <boolProp name="ThreadGroup.same_user_on_next_iteration">true</boolProp>
      </ThreadGroup>
      <hashTree>
        <ConstantTimer guiclass="ConstantTimerGui" testclass="ConstantTimer" testname="Think Time" enabled="true">
          <stringProp name="ConstantTimer.delay">1000</stringProp>
        </ConstantTimer>
        <hashTree/>
        <HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="HTTP Request" enabled="true">
          <elementProp name="HTTPsampler.Arguments" elementType="Arguments" guiclass="HTTPArgumentsPanel" testclass="Arguments" testname="User Defined Variables" enabled="true">
            <collectionProp name="Arguments.arguments"/>
          </elementProp>
          <stringProp name="HTTPSampler.domain">example.com</stringProp>
          <stringProp name="HTTPSampler.port"></stringProp>
          <stringProp name="HTTPSampler.protocol">https</stringProp>
          <stringProp name="HTTPSampler.contentEncoding"></stringProp>
          <stringProp name="HTTPSampler.path">/</stringProp>
          <stringProp name="HTTPSampler.method">GET</stringProp>
          <boolProp name="HTTPSampler.follow_redirects">true</boolProp>
          <boolProp name="HTTPSampler.auto_redirects">false</boolProp>
          <boolProp name="HTTPSampler.use_keepalive">true</boolProp>
          <boolProp name="HTTPSampler.DO_MULTIPART_POST">false</boolProp>
          <stringProp name="HTTPSampler.embedded_url_re"></stringProp>
          <stringProp name="HTTPSampler.connect_timeout"></stringProp>
          <stringProp name="HTTPSampler.response_timeout"></stringProp>
        </HTTPSamplerProxy>
        <hashTree/>
      </hashTree>
      <ResultCollector guiclass="ViewResultsFullVisualizer" testclass="ResultCollector" testname="View Results Tree" enabled="true">
        <boolProp name="ResultCollector.error_logging">false</boolProp>
        <objProp>
          <name>saveConfig</name>
          <value class="SampleSaveConfiguration">
            <time>true</time>
            <latency>true</latency>
            <timestamp>true</timestamp>
            <success>true</success>
            <label>true</label>
            <code>true</code>
            <message>true</message>
            <threadName>true</threadName>
            <dataType>true</dataType>
            <encoding>false</encoding>
            <subresults>true</subresults>
            <responseData>false</responseData>
            <samplerData>false</samplerData>
            <xml>false</xml>
            <fieldNames>true</fieldNames>
            <responseHeaders>false</responseHeaders>
            <requestHeaders>false</requestHeaders>
            <responseDataOnError>false</responseDataOnError>
            <saveAssertionResultsFailureMessage>true</saveAssertionResultsFailureMessage>
            <assertionsResultsToSave>0</assertionsResultsToSave>
            <bytes>true</bytes>
            <sentBytes>true</sentBytes>
            <url>true</url>
            <threadCounts>true</threadCounts>
            <idleTime>true</idleTime>
            <connectTime>true</connectTime>
          </value>
        </objProp>
        <stringProp name="filename"></stringProp>
      </ResultCollector>
      <hashTree/>
      <ResultCollector guiclass="SummaryReport" testclass="ResultCollector" testname="Summary Report" enabled="true">
        <boolProp name="ResultCollector.error_logging">false</boolProp>
        <objProp>
          <name>saveConfig</name>
          <value class="SampleSaveConfiguration">
            <time>true</time>
            <latency>true</latency>
            <timestamp>true</timestamp>
            <success>true</success>
            <label>true</label>
            <code>true</code>
            <message>true</message>
            <threadName>true</threadName>
            <dataType>true</dataType>
            <encoding>false</encoding>
            <subresults>true</subresults>
            <responseData>false</responseData>
            <samplerData>false</samplerData>
            <xml>false</xml>
            <fieldNames>true</fieldNames>
            <responseHeaders>false</responseHeaders>
            <requestHeaders>false</requestHeaders>
            <responseDataOnError>false</responseDataOnError>
            <saveAssertionResultsFailureMessage>true</saveAssertionResultsFailureMessage>
            <assertionsResultsToSave>0</assertionsResultsToSave>
            <bytes>true</bytes>
            <sentBytes>true</sentBytes>
            <url>true</url>
            <threadCounts>true</threadCounts>
            <idleTime>true</idleTime>
            <connectTime>true</connectTime>
          </value>
        </objProp>
        <stringProp name="filename"></stringProp>
      </ResultCollector>
      <hashTree/>
    </hashTree>
  </hashTree>
</jmeterTestPlan>"""

    def save_jmx(self, jmx_content, test_type):
        """Save the JMX file in the jmeter-tests/test-plans directory"""
        # Create directory if it doesn't exist
        os.makedirs('jmeter-tests/test-plans', exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"jmeter-tests/test-plans/{test_type.lower().replace(' ', '_')}_{timestamp}.jmx"
        
        # Save the JMX content
        with open(filename, 'w') as f:
            f.write(jmx_content)
        
        return filename

    def _validate_jmeter_compatibility(self, xml_content):
        """Remove any incompatible JMeter elements from the XML content"""
        # List of incompatible elements that should be removed
        incompatible_elements = [
            'ResponseTimeAssertion',
            'DebugSampler',
            'BSFSampler',
            'BSFPreProcessor',
            'BSFPostProcessor',
            'BSFAssertion',
            'BeanShellSampler',  # Deprecated in newer versions
            'AjpSampler',
            'GraphVisualizer',   # Removed in newer versions
            'ComparisonVisualizer',
            'MonitorHealthVisualizer',
            'DisableAction'
        ]
        
        # Check and remove any incompatible elements
        for element in incompatible_elements:
            if element in xml_content:
                print(f"Warning: Removing incompatible element '{element}' from JMX")
                # Simple replacement - removes the element and its content
                pattern = re.compile(f'<{element}.*?</{element}>', re.DOTALL)
                xml_content = pattern.sub('', xml_content)
                
                # Also remove any empty hashTree elements that might be left behind
                xml_content = re.sub(r'<hashTree>\s*</hashTree>', '', xml_content)
        
        return xml_content

def main():
    assistant = PerformanceTestAssistant()
    
    print("Welcome to the JMeter Test Plan Generator!")
    print("\nDescribe what you want to test, and I'll help you create a JMeter test plan.")
    print("\nExamples:")
    print("- 'I want to test my mobile app API at https://api.example.com'")
    print("- 'Need to load test my web application with 500 concurrent users'")
    print("- 'I want to stress test my database with sudden spikes in traffic'")
    print("- 'Need to test my REST API with different HTTP methods'")
    
    while True:
        user_input = input("\nWhat would you like to test? ").strip()
        
        # Get initial test setup suggestion
        setup = assistant.get_test_setup_suggestion(user_input)
        print("\nHere's my suggested test setup:")
        print(setup)
        
        while True:
            print("\nWhat would you like to do?")
            print("1. Accept this setup and generate JMX")
            print("2. Modify the setup")
            print("3. Start over with a new test")
            print("4. Exit")
            
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == "1":
                print("\nGenerating JMX file...")
                jmx = assistant.generate_jmx(setup)
                # Extract test type from the setup for filename
                test_type = user_input.split(' ')[4] if len(user_input.split(' ')) > 4 else "performance_test"
                filename = assistant.save_jmx(jmx, test_type)
                print(f"\nJMX file has been generated and saved to: {filename}")
                print("\nWould you like to create another test plan? (y/n)")
                if input().lower() != 'y':
                    print("Goodbye!")
                    return
                break
                
            elif choice == "2":
                print("\nWhat changes would you like to make?")
                print("Examples:")
                print("- 'Change the number of users to 200'")
                print("- 'Add a 2-second think time'")
                print("- 'Include authentication headers'")
                print("- 'Add response assertions'")
                feedback = input("\nYour changes: ").strip()
                setup = assistant.refine_setup(feedback)
                print("\nUpdated test setup:")
                print(setup)
                
            elif choice == "3":
                break
                
            elif choice == "4":
                print("Goodbye!")
                return
                
            else:
                print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main() 