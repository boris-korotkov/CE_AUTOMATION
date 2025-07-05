import yaml
import logging
import os
import time
from jinja2 import Template, Environment
import ce_actions

# Setup a Jinja2 environment that includes the 'len' function
jinja_env = Environment()
jinja_env.globals['len'] = len

class WorkflowEngine:
    def __init__(self, adb_id, language, instance_name):
        self.adb_id = adb_id
        self.language = language
        self.context = {'instance_name': instance_name}
        self.actions = {
            'click': lambda args: ce_actions.click(self.adb_id, *args),
            'delay': lambda args: time.sleep(args),
            'scroll': lambda args: ce_actions.scroll(self.adb_id, *args),
            'send_email': lambda args: ce_actions.send_email("CE Automation Notification", self._render_template_string(args)),
            'log': lambda args: logging.info(f"[WORKFLOW] {self._render_template_string(args)}"),
            'emergency_exit': lambda args: ce_actions.emergency_exit(args)
        }
        self.conditional_actions = {
            'compare_with_image': lambda *args: ce_actions.compare_with_image(self.adb_id, self.language, self.context['instance_name'], *args),
            'compare_with_text': lambda *args: ce_actions.compare_with_text(self.adb_id, self.language, self.context['instance_name'], *args),
            'compare_with_any_image': lambda *args: ce_actions.compare_with_any_image(self.adb_id, self.language, self.context['instance_name'], *args),
            'compare_with_text_easyocr': lambda *args: ce_actions.compare_with_text_easyocr(self.adb_id, self.language, self.context['instance_name'], *args),
            'compare_with_features': lambda *args: ce_actions.compare_with_features(self.adb_id, self.language, self.context['instance_name'], *args),
            'get_coords_from_image': lambda *args: ce_actions.get_coords_from_image(self.adb_id, self.language, *args),
            'get_all_coords_from_image': lambda *args: ce_actions.get_all_coords_from_image(self.adb_id, self.language, *args),
            'get_coords_from_features': lambda *args: ce_actions.get_coords_from_features(self.adb_id, self.language, *args),
            'get_all_coords_from_features': lambda *args: ce_actions.get_all_coords_from_features(self.adb_id, self.language, *args),
        }

    def _render_template_string(self, template_string):
        """Renders a single string using Jinja2, returning a string."""
        if not isinstance(template_string, str):
            return template_string
        template = jinja_env.from_string(template_string)
        # The full context includes variables and callable functions
        full_context = {**self.context, **self.conditional_actions}
        return template.render(full_context)
    
    # --- THIS IS THE NEW, ROBUST RENDERER ---
    def _render_params(self, params):
        """
        Recursively processes parameters. It renders Jinja2 templates in strings
        and then evaluates the result to get the final Python object.
        It handles lists and dictionaries correctly without trying to eval the whole structure.
        """
        if isinstance(params, str):
            # Step 1: Render the Jinja2 template string
            rendered_string = self._render_template_string(params)
            # Step 2: Try to evaluate the result to a Python object
            try:
                # This safely converts " (1, 2) " into a tuple, "123" into an int, etc.
                return eval(rendered_string, {'__builtins__': {}}, {})
            except (SyntaxError, TypeError, NameError):
                # If eval fails, it was just a regular string. Return it as is.
                return rendered_string
        elif isinstance(params, list):
            # If it's a list, process each item individually
            return [self._render_params(item) for item in params]
        elif isinstance(params, dict):
            # If it's a dictionary, process each value individually
            return {key: self._render_params(value) for key, value in params.items()}
        else:
            # Return numbers, booleans, etc. as-is
            return params

    def _evaluate_condition(self, condition_str):
        """Evaluates a condition string to True or False."""
        logging.debug(f"Evaluating condition: {condition_str}")
        try:
            eval_globals = {'__builtins__': None, 'len': len} # Add len to conditions as well
            eval_locals = {**self.context, **self.conditional_actions}
            return eval(condition_str, eval_globals, eval_locals)
        except Exception as e:
            logging.error(f"Error evaluating condition '{condition_str}': {type(e).__name__}: {e}")
            return False

    def _process_steps(self, steps):
        if steps is None: 
            logging.error("A 'then' or 'do' block in the workflow is empty."); return
        for step in steps:
            if not isinstance(step, dict): 
                logging.error(f"Malformed step found in workflow: {step}"); continue
            
            command = list(step.keys())[0]
            raw_params = step[command]
            
            if raw_params is None and command not in ['if', 'while']:
                 logging.error(f"Malformed step: command '{command}' has no value."); continue

            if command in ['if', 'while']:
                # Structural commands use the raw condition string
                condition_result = self._evaluate_condition(raw_params['condition'])
                if command == 'if':
                    if condition_result: self._process_steps(raw_params.get('then'))
                    elif 'else' in raw_params: self._process_steps(raw_params.get('else'))
                elif command == 'while' and condition_result:
                    while self._evaluate_condition(raw_params['condition']):
                        self._process_steps(raw_params.get('do'))
            else:
                # Action commands have their parameters fully rendered
                rendered_params = self._render_params(raw_params)
                
                if command in self.actions:
                    if isinstance(rendered_params, list) and command in ['click', 'scroll']:
                        self.actions[command](rendered_params)
                    else:
                        self.actions[command](rendered_params)
                elif command == 'set':
                    self.context.update(rendered_params)
                    logging.debug(f"Context updated: {self.context}")
                elif command == 'increment':
                    self.context[raw_params] = self.context.get(raw_params, 0) + 1
                    logging.debug(f"Incremented '{raw_params}': {self.context[raw_params]}")
                else:
                    logging.warning(f"Unknown command in workflow: {command}")

    def run_workflow(self, workflow_name):
        yaml_path = os.path.join("resources", self.language, "workflows.yaml")
        if not os.path.exists(yaml_path): logging.error(f"Workflow file not found: {yaml_path}"); return
        with open(yaml_path, 'r') as f: data = yaml.safe_load(f)
        target_scenario = next((s for s in data.get('scenarios', []) if s.get('name') == workflow_name), None)
        if not target_scenario: logging.error(f"Workflow '{workflow_name}' not found"); return
        if 'steps' not in target_scenario or not target_scenario['steps']: logging.error(f"Workflow '{workflow_name}' has no steps."); return
        logging.info(f"Executing workflow: {workflow_name} - {target_scenario.get('description', '')}")
        self._process_steps(target_scenario['steps'])
        logging.info(f"Finished workflow: {workflow_name}")