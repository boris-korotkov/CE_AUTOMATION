import yaml
import logging
import os
import time
from jinja2 import Template
import ce_actions

class WorkflowEngine:
    def __init__(self, adb_id, language):
        self.adb_id = adb_id
        self.language = language
        self.context = {}
        self.actions = {
            'click': lambda args: ce_actions.click(self.adb_id, *args),
            'delay': lambda args: time.sleep(args),
            'scroll': lambda args: ce_actions.scroll(self.adb_id, *args),
            'send_email': lambda args: ce_actions.send_email("CE Automation Notification", args),
            'log': lambda args: logging.info(f"[WORKFLOW] {self._render_template(args)}"),
            'emergency_exit': lambda args: ce_actions.emergency_exit(args)
        }
        self.conditional_actions = {
            'compare_with_image': lambda *args: ce_actions.compare_with_image(self.adb_id, self.language, *args),
            'compare_with_text': lambda *args: ce_actions.compare_with_text(self.adb_id, self.language, *args),
            'compare_with_any_image': lambda *args: ce_actions.compare_with_any_image(self.adb_id, self.language, *args)
        }

    def _render_template(self, template_string):
        return Template(template_string).render(self.context)

    def _evaluate_condition(self, condition_str):
        logging.debug(f"Evaluating condition: {condition_str}")
        try:
            eval_globals = {'__builtins__': None}
            eval_locals = {**self.context, **self.conditional_actions}
            return eval(condition_str, eval_globals, eval_locals)
        except Exception as e:
            logging.error(f"Error evaluating condition '{condition_str}': {type(e).__name__}: {e}")
            return False

    def _process_steps(self, steps):
        """Recursively processes a list of steps from the workflow."""
        if steps is None:
            logging.error("A 'then' or 'do' block in the workflow is empty. Please check your YAML file.")
            return

        for step in steps:
            if not isinstance(step, dict):
                logging.error(f"Malformed step found in workflow. It should be a dictionary (e.g., 'click: [x,y]'). Step: {step}")
                continue

            command = list(step.keys())[0]
            params = step[command]

            # --- NEW ROBUSTNESS CHECK ---
            # Check if a command is missing its value (e.g., "if:")
            if params is None:
                logging.error(f"Malformed step found in workflow. The command '{command}' has no value. Please check your YAML indentation and structure.")
                continue # Skip this broken step

            if command in self.actions:
                self.actions[command](params)
            elif command == 'set':
                self.context.update(params)
                logging.debug(f"Context updated: {self.context}")
            elif command == 'increment':
                self.context[params] = self.context.get(params, 0) + 1
                logging.debug(f"Incremented '{params}': {self.context[params]}")
            elif command == 'if':
                if self._evaluate_condition(params['condition']):
                    self._process_steps(params.get('then')) # Use .get() for safety
                elif 'else' in params:
                    self._process_steps(params.get('else'))
            elif command == 'while':
                while self._evaluate_condition(params['condition']):
                    self._process_steps(params.get('do'))
            else:
                logging.warning(f"Unknown command in workflow: {command}")

    def run_workflow(self, workflow_name):
        # ... (This function remains unchanged) ...
        yaml_path = os.path.join("resources", self.language, "workflows.yaml")
        if not os.path.exists(yaml_path):
            logging.error(f"Workflow file not found for language '{self.language}': {yaml_path}")
            return
            
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)

        target_scenario = next((s for s in data['scenarios'] if s['name'] == workflow_name), None)
        
        if not target_scenario:
            logging.error(f"Workflow '{workflow_name}' not found in {yaml_path}")
            return
        
        # Check if the 'steps' key exists and is not empty
        if 'steps' not in target_scenario or not target_scenario['steps']:
             logging.error(f"Workflow '{workflow_name}' has no steps defined. Skipping.")
             return

        logging.info(f"Executing workflow: {workflow_name} - {target_scenario.get('description', '')}")
        self._process_steps(target_scenario['steps'])
        logging.info(f"Finished workflow: {workflow_name}")