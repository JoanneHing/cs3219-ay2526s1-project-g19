"""
Execution service views for code execution and testing.
"""
import os
import requests
import concurrent.futures
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

logger = logging.getLogger(__name__)

# Configuration from Django settings
JUDGE0_URL = os.getenv('JUDGE0_URL', 'http://judge0:2358')
JUDGE0_API_KEY = os.getenv('JUDGE0_API_KEY', '')
QUESTION_SERVICE_URL = os.getenv('QUESTION_SERVICE_URL', 'http://question-service:8000')

# Language mapping for common languages
LANGUAGE_MAP = {
    'python3': 71,
    'python': 71,
    'javascript': 63,
    'node': 63,
    'java': 62,
    'cpp': 54,
    'c': 50,
    'csharp': 51,
    'go': 60,
    'rust': 73,
    'php': 68,
    'ruby': 72,
    'swift': 83,
    'kotlin': 78,
    'scala': 81,
    'typescript': 74,
}

class ExecuteView(APIView):
    """
    Execute a single code snippet with optional input.
    """
    
    @extend_schema(
        summary="Execute code",
        description="Execute a single code snippet and return the output.",
        request={
            'type': 'object',
            'properties': {
                'language_id': {
                    'type': 'integer',
                    'description': 'Judge0 language ID (e.g., 71 for Python 3)',
                    'example': 71
                },
                'source_code': {
                    'type': 'string',
                    'description': 'Source code to execute',
                    'example': 'print("Hello, World!")'
                },
                'stdin': {
                    'type': 'string',
                    'description': 'Standard input for the program',
                    'example': 'test input',
                    'default': ''
                }
            },
            'required': ['language_id', 'source_code']
        },
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'status': {'type': 'string', 'example': 'Accepted'},
                    'stdout': {'type': 'string', 'example': 'Hello, World!\n'},
                    'stderr': {'type': 'string', 'example': ''},
                    'time': {'type': 'string', 'example': '0.05'},
                    'memory': {'type': 'integer', 'example': 12345},
                    'compile_output': {'type': 'string', 'example': ''}
                }
            },
            400: {'description': 'Invalid input'},
            502: {'description': 'Execution service error'}
        },
        tags=['execution']
    )
    def post(self, request):
        """Execute code and return results."""
        language_id = request.data.get('language_id')
        source_code = request.data.get('source_code')
        stdin = request.data.get('stdin', '')
        
        if not language_id or not source_code:
            return Response(
                {'error': 'language_id and source_code are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Prepare Judge0 submission
            payload = {
                'language_id': language_id,
                'source_code': source_code,
                'stdin': stdin
            }
            
            # Submit to Judge0 with synchronous execution
            judge0_url = f"{JUDGE0_URL}/submissions"
            headers = {}
            if JUDGE0_API_KEY:
                headers['X-RapidAPI-Key'] = JUDGE0_API_KEY
                headers['X-RapidAPI-Host'] = 'ce.judge0.com'
            
            response = requests.post(
                f"{judge0_url}?base64_encoded=false&wait=true",
                json=payload,
                headers=headers,
                timeout=20
            )
            
            if response.status_code >= 400:
                logger.error(f"Judge0 error: {response.status_code} - {response.text}")
                return Response(
                    {'error': 'execution_failed', 'details': response.text},
                    status=status.HTTP_502_BAD_GATEWAY
            )
            
            data = response.json()
            
            # Normalize response
            result = {
                'status': data.get('status', {}).get('description', 'Unknown'),
                'stdout': data.get('stdout', ''),
                'stderr': data.get('stderr', ''),
                'time': data.get('time', ''),
                'memory': data.get('memory', 0),
                'compile_output': data.get('compile_output', ''),
            }
            
            logger.info(f"Code executed successfully: {result['status']}")
            return Response(result, status=status.HTTP_200_OK)
            
        except requests.exceptions.Timeout:
            logger.error("Execution timeout")
            return Response(
                {'error': 'execution_timeout'}, 
                status=status.HTTP_502_BAD_GATEWAY
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            return Response(
                {'error': 'execution_service_unavailable'}, 
                status=status.HTTP_502_BAD_GATEWAY
            )
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return Response(
                {'error': 'internal_error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ExecuteTestsView(APIView):
    """
    Execute code against official test cases from question service.
    """
    
    @extend_schema(
        summary="Execute code against test cases",
        description="Execute code against official test cases from question service.",
        request={
            'type': 'object',
            'properties': {
                'language_id': {
                    'type': 'integer',
                    'description': 'Judge0 language ID',
                    'example': 71
                },
                'source_code': {
                    'type': 'string',
                    'description': 'Source code to execute',
                    'example': 'print(input())'
                },
                'question_id': {
                    'type': 'string',
                    'description': 'Question ID to fetch test cases from',
                    'example': '123e4567-e89b-12d3-a456-426614174000'
                }
            },
            'required': ['language_id', 'source_code', 'question_id']
        },
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'summary': {
                        'type': 'object',
                        'properties': {
                            'passed': {'type': 'integer', 'example': 2},
                            'total': {'type': 'integer', 'example': 3}
                        }
                    },
                    'results': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'ok': {'type': 'boolean'},
                                'status': {'type': 'string'},
                                'stdout': {'type': 'string'},
                                'expected': {'type': 'string'},
                                'stderr': {'type': 'string'},
                                'time': {'type': 'string'},
                                'memory': {'type': 'integer'}
                            }
                        }
                    }
                }
            },
            400: {'description': 'Invalid input'},
            502: {'description': 'Service error'}
        },
        tags=['execution']
    )
    def post(self, request):
        """Execute code against test cases."""
        language_id = request.data.get('language_id')
        source_code = request.data.get('source_code')
        question_id = request.data.get('question_id')
        
        if not all([language_id, source_code, question_id]):
            return Response(
                {'error': 'language_id, source_code, and question_id are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Fetch test cases from question service
            question_url = f"{QUESTION_SERVICE_URL}/api/questions/{question_id}?fields=examples"
            question_response = requests.get(question_url, timeout=10)
            
            if question_response.status_code != 200:
                logger.error(f"Question service error: {question_response.status_code}")
                return Response(
                    {'error': 'question_fetch_failed'}, 
                    status=status.HTTP_502_BAD_GATEWAY
                )
            
            question_data = question_response.json()
            examples = question_data.get('examples', [])
            
            if not examples:
                return Response(
                    {'error': 'no_test_cases_found'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Execute each test case
            def run_test_case(case):
                """Run a single test case."""
                try:
                    test_input = case.get('input', '')
                    expected_output = case.get('output', '')
                    
                    payload = {
                        'language_id': language_id,
                        'source_code': source_code,
                        'stdin': test_input
                    }
                    
                    judge0_url = f"{JUDGE0_URL}/submissions"
                    headers = {}
                    if JUDGE0_API_KEY:
                        headers['X-RapidAPI-Key'] = JUDGE0_API_KEY
                        headers['X-RapidAPI-Host'] = 'ce.judge0.com'
                    
                    response = requests.post(
                        f"{judge0_url}?base64_encoded=false&wait=true",
                        json=payload,
                        headers=headers,
                        timeout=20
                    )
                    
                    if response.status_code >= 400:
                        return {
                            'ok': False,
                            'error': 'exec_failed',
                            'status': 'Error',
                            'stdout': '',
                            'expected': expected_output,
                            'stderr': response.text,
                            'time': '0',
                            'memory': 0
                        }
                    
                    data = response.json()
                    stdout = (data.get('stdout') or '').strip()
                    expected = expected_output.strip()
                    status_desc = data.get('status', {}).get('description', 'Unknown')
                    
                    return {
                        'ok': stdout == expected and status_desc == 'Accepted',
                        'status': status_desc,
                        'stdout': stdout,
                        'expected': expected,
                        'stderr': data.get('stderr', ''),
                        'time': data.get('time', ''),
                        'memory': data.get('memory', 0),
                    }
                    
                except Exception as e:
                    logger.error(f"Test case execution error: {e}")
                    return {
                        'ok': False,
                        'error': 'exec_failed',
                        'status': 'Error',
                        'stdout': '',
                        'expected': case.get('output', ''),
                        'stderr': str(e),
                        'time': '0',
                        'memory': 0
                    }
            
            # Run all test cases in parallel
            results = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                results = list(executor.map(run_test_case, examples))
            
            # Calculate summary
            passed = sum(1 for result in results if result.get('ok', False))
            total = len(results)
            
            response_data = {
                'summary': {
                    'passed': passed,
                    'total': total
                },
                'results': results
            }
            
            logger.info(f"Test execution completed: {passed}/{total} passed")
            return Response(response_data, status=status.HTTP_200_OK)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            return Response(
                {'error': 'service_unavailable'}, 
                status=status.HTTP_502_BAD_GATEWAY
            )
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return Response(
                {'error': 'internal_error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LanguagesView(APIView):
    """
    Get supported programming languages.
    """
    
    @extend_schema(
        summary="Get supported languages",
        description="Get list of supported programming languages with their Judge0 IDs.",
        responses={
            200: {
                'type': 'object',
                'properties': {
                    'languages': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'name': {'type': 'string', 'example': 'python3'},
                                'id': {'type': 'integer', 'example': 71},
                                'display_name': {'type': 'string', 'example': 'Python 3'}
                            }
                        }
                    }
                }
            }
        },
        tags=['execution']
    )
    def get(self, request):
        """Get supported programming languages."""
        languages = []
        for name, lang_id in LANGUAGE_MAP.items():
            display_name = name.replace('_', ' ').title()
            if name == 'python3':
                display_name = 'Python 3'
            elif name == 'cpp':
                display_name = 'C++'
            elif name == 'csharp':
                display_name = 'C#'
            elif name == 'javascript':
                display_name = 'JavaScript'
            elif name == 'node':
                display_name = 'Node.js'
            
            languages.append({
                'name': name,
                'id': lang_id,
                'display_name': display_name
            })
        
        return Response({'languages': languages}, status=status.HTTP_200_OK)


