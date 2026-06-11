{{/*
Common labels for all resources.
*/}}
{{- define "ecole.labels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end }}

{{/*
Selector labels for a specific component.
*/}}
{{- define "ecole.selectorLabels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: {{ .component }}
{{- end }}

{{/*
Full name prefix. If the release name already contains the chart name, use
the release name alone to avoid duplication (e.g. "ecole-platform-ecole-platform").
*/}}
{{- define "ecole-platform.fullname" -}}
{{- if contains .Chart.Name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{/*
Service account name — defaults to chart fullname when serviceAccount.create is true.
*/}}
{{- define "ecole-platform.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "ecole-platform.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}
