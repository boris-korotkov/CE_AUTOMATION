import yaml
import logging
import os
import time
from jinja2 import Template, Environment
import ce_actions
from datetime import datetime

# Setup a Jinja2 environment that includes the 'len' function
jinja_env = Environment()
jinja_env.globals['len'] = len

class WorkflowEngine:
    def __init__(self, adb_id, language, instance_name, workflow_file=None):
        self.adb_id = adb_id
        self.language = language
        self.context = {'instance_name': instance_name}
        self.workflow_file = workflow_file
        self.actions = {
            'click': lambda args: ce_actions.click(self.adb_id, *args),
            'delay': lambda args: time.sleep(args),
            'scroll': lambda args: ce_actions.scroll(self.adb_id, *args),
            'send_email': lambda args: ce_actions.send_email(
                subject=f"CE Automation Notification - {datetime.now().strftime('%Y-%m-%d')}",
                body=self._render_template_string(args)
            ),
            'log': lambda args: logging.info(f"[WORKFLOW] {self._render_template_string(args)}"),
            'emergency_exit': lambda args: ce_actions.emergency_exit(args)
        }
        self.conditional_actions = {
             'compare_with_image': lambda *args: ce_actions.compare_with_image(self.adb_id, self.language, self.context.get('instance_name'), self.context.get('workflow_name'), *args),
            'compare_with_text': lambda *args: ce_actions.compare_with_text(self.adb_id, self.language, self.context.get('instance_name'), self.context.get('workflow_name'), *args),
            'compare_with_any_image': lambda *args: ce_actions.compare_with_any_image(self.adb_id, self.language, self.context.get('instance_name'), self.context.get('workflow_name'), *args),
            'compare_with_text_easyocr': lambda *args: ce_actions.compare_with_text_easyocr(self.adb_id, self.language, self.context.get('instance_name'), self.context.get('workflow_name'), *args),
            'compare_with_features': lambda *args: ce_actions.compare_with_features(self.adb_id, self.language, self.context.get('instance_name'), self.context.get('workflow_name'), *args),
            'get_coords_from_image': lambda *args: ce_actions.get_coords_from_image(self.adb_id, self.language, self.context.get('instance_name'), self.context.get('workflow_name'), *args),
            'get_all_coords_from_image': lambda *args: ce_actions.get_all_coords_from_image(self.adb_id, self.language, self.context.get('instance_name'), self.context.get('workflow_name'), *args),
            'get_coords_from_features': lambda *args: ce_actions.get_coords_from_features(self.adb_id, self.language, self.context.get('instance_name'), self.context.get('workflow_name'), *args),
            'get_all_coords_from_features': lambda *args: ce_actions.get_all_coords_from_features(self.adb_id, self.language, self.context.get('instance_name'), self.context.get('workflow_name'), *args),
        }

    def _render_template_string(self, template_string):
        """Renders a single string using Jinja2, returning a string."""
        if not isinstance(template_string, str):
            return template_string
        template = jinja_env.from_string(template_string)
        full_context = {**self.context, **self.conditional_actions}
        full_context['current_date'] = datetime.now().strftime("%Y-%m-%d")
        
        return template.render(full_context)
    
    def _render_params(self, params):
        """
        Recursively processes parameters, rendering Jinja2 templates and evaluating the result.
        """
        if isinstance(params, str):
            rendered_string = self._render_template_string(params)
            try:
                return eval(rendered_string, {'__builtins__': {}}, {})
            except (SyntaxError, TypeError, NameError):
                return rendered_string
        elif isinstance(params, list):
            return [self._render_params(item) for item in params]
        elif isinstance(params, dict):
            return {key: self._render_params(value) for key, value in params.items()}
        else:
            return params

    def _evaluate_condition(self, condition_str):
        """Evaluates a condition string to True or False."""
        logging.debug(f"Evaluating condition: {condition_str}")
        try:
            eval_globals = {'__builtins__': None, 'len': len}
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
                condition_result = self._evaluate_condition(raw_params['condition'])
                if command == 'if':
                    if condition_result: self._process_steps(raw_params.get('then'))
                    elif 'else' in raw_params: self._process_steps(raw_params.get('else'))
                elif command == 'while' and condition_result:
                    while self._evaluate_condition(raw_params['condition']):
                        self._process_steps(raw_params.get('do'))
            else:
                rendered_params = self._render_params(raw_params)
                if rendered_params is None and command not in ['set']: # 'set' can have None value from get_coords
                    logging.error(f"Rendered parameters for command '{command}' are None. Check your YAML variables."); continue

                if command in self.actions:
                    if isinstance(rendered_params, list) and command in ['click', 'scroll']:
                        self.actions[command](rendered_params)
                    else:
                        self.actions[command](rendered_params)
                elif command == 'set':
                    if rendered_params is None: # Handle case where a function returns None
                        key = list(raw_params.keys())[0]
                        self.context[key] = None
                        logging.debug(f"Context updated: {key} set to None")
                    else:
                        self.context.update(rendered_params)
                        logging.debug(f"Context updated: {self.context}")
                elif command == 'increment':
                    self.context[raw_params] = self.context.get(raw_params, 0) + 1
                    logging.debug(f"Incremented '{raw_params}': {self.context[raw_params]}")
                else:
                    logging.warning(f"Unknown command in workflow: {command}")

    def run_workflow(self, workflow_name):
        if self.workflow_file:
            yaml_path = self.workflow_file
        else:
            yaml_path = os.path.join("resources", self.language, "workflows.yaml")
        
        if not os.path.exists(yaml_path):
            logging.error(f"Workflow file not found: {yaml_path}"); return
        
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        
        target_scenario = next((s for s in data.get('scenarios', []) if s.get('name') == workflow_name), None)
        
        if not target_scenario:
            logging.error(f"Workflow '{workflow_name}' not found in {yaml_path}"); return
        if 'steps' not in target_scenario or not target_scenario['steps']:
            logging.error(f"Workflow '{workflow_name}' has no steps."); return
            
        logging.info(f"Executing workflow: {workflow_name} from '{os.path.basename(yaml_path)}' - {target_scenario.get('description', '')}")
        self.context['workflow_name'] = workflow_name
        self._process_steps(target_scenario['steps'])
        logging.info(f"Finished workflow: {workflow_name}")