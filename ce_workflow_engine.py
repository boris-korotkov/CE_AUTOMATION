import yaml
import logging
import os
import time
from jinja2 import Template, UndefinedError
import ce_actions

class WorkflowEngine:
    def __init__(self, adb_id, language, instance_name):
        self.adb_id = adb_id
        self.language = language
        self.context = {'instance_name': instance_name}
        self.actions = {
            'click': lambda args: ce_actions.click(self.adb_id, *args),
            'delay': lambda args: time.sleep(args),
            'scroll': lambda args: ce_actions.scroll(self.adb_id, *args),
            'send_email': lambda args: ce_actions.send_email("CE Automation Notification", self._render_template(args)),
            'log': lambda args: logging.info(f"[WORKFLOW] {self._render_template(args)}"),
            'emergency_exit': lambda args: ce_actions.emergency_exit(args)
        }
        self.conditional_actions = {
            'compare_with_image': lambda *args: ce_actions.compare_with_image(self.adb_id, self.language, self.context['instance_name'], *args),
            'compare_with_text': lambda *args: ce_actions.compare_with_text(self.adb_id, self.language, self.context['instance_name'], *args),
            'compare_with_any_image': lambda *args: ce_actions.compare_with_any_image(self.adb_id, self.language, self.context['instance_name'], *args),
            'compare_with_text_easyocr': lambda *args: ce_actions.compare_with_text_easyocr(self.adb_id, self.language, self.context['instance_name'], *args),
            'compare_with_features': lambda *args: ce_actions.compare_with_features(self.adb_id, self.language, self.context['instance_name'], *args),
            'get_coords_from_image': lambda *args: ce_actions.get_coords_from_image(self.adb_id, self.language, *args)
        }

    def _render_template(self, template_string):
        full_context = {**self.context, **self.conditional_actions}
        return Template(str(template_string)).render(full_context)

    def _render_params(self, params):
        if isinstance(params, str):
            full_context = {**self.context, **self.conditional_actions}
            rendered_template = Template(params).render(full_context)
            try:
                # Using a safe eval to convert string representations like "(1,2)" into Python objects
                return eval(rendered_template, {'__builtins__':{}}, {})
            except (SyntaxError, TypeError, NameError):
                # If eval fails, the result was likely just a plain string.
                return rendered_template
        elif isinstance(params, list):
            return [self._render_params(item) for item in params]
        elif isinstance(params, dict):
            return {key: self._render_params(value) for key, value in params.items()}
        else:
            return params

    def _evaluate_condition(self, condition_str):
        logging.debug(f"Evaluating condition: {condition_str}")
        try:
            eval_globals = {'__builtins__': None}
            eval_locals = {**self.context, **self.conditional_actions}
            return eval(condition_str, eval_globals, eval_locals)
        except Exception as e:
            logging.error(f"Error evaluating condition '{condition_str}': {type(e).__name__}: {e}"); return False

    # --- THIS IS THE CORRECTED METHOD ---
    def _process_steps(self, steps):
        if steps is None: 
            logging.error("A 'then' or 'do' block in the workflow is empty."); return
        for step in steps:
            if not isinstance(step, dict): 
                logging.error(f"Malformed step found in workflow: {step}"); continue
            
            command = list(step.keys())[0]
            # Get the original, raw parameters
            raw_params = step[command]
            
            if raw_params is None:
                 logging.error(f"Malformed step: command '{command}' has no value."); continue

            # Handle structural commands first, as they need the raw condition string
            if command == 'if':
                if self._evaluate_condition(raw_params['condition']):
                    self._process_steps(raw_params.get('then'))
                elif 'else' in raw_params:
                    self._process_steps(raw_params.get('else'))
            elif command == 'while':
                while self._evaluate_condition(raw_params['condition']):
                    self._process_steps(raw_params.get('do'))
            
            # For all other "action" commands, render their parameters now
            else:
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
                    # Increment needs the raw key, not the rendered one
                    self.context[raw_params] = self.context.get(raw_params, 0) + 1
                    logging.debug(f"Incremented '{raw_params}': {self.context[raw_params]}")
                else:
                    logging.warning(f"Unknown command in workflow: {command}")


    def run_workflow(self, workflow_name):
        # ... (This function is unchanged) ...
        yaml_path = os.path.join("resources", self.language, "workflows.yaml")
        if not os.path.exists(yaml_path): logging.error(f"Workflow file not found for language '{self.language}': {yaml_path}"); return
        with open(yaml_path, 'r') as f: data = yaml.safe_load(f)
        target_scenario = next((s for s in data.get('scenarios', []) if s.get('name') == workflow_name), None)
        if not target_scenario: logging.error(f"Workflow '{workflow_name}' not found in {yaml_path}"); return
        if 'steps' not in target_scenario or not target_scenario['steps']: logging.error(f"Workflow '{workflow_name}' has no steps defined. Skipping."); return
        logging.info(f"Executing workflow: {workflow_name} - {target_scenario.get('description', '')}")
        self._process_steps(target_scenario['steps'])
        logging.info(f"Finished workflow: {workflow_name}")