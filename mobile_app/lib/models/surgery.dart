/// Represents a surgery procedure record.
///
/// Contains patient information, scheduling details, and medical notes
/// across the surgical workflow (prep, intra-op, post-op).
class Surgery {
  final int? id;
  final String patientName;
  final String hospital;
  final String surgeryType;
  final String scheduledDate;
  final String status;
  final String? prepChecklist;
  final String? intraOpNotes;
  final String? postOpReport;

  const Surgery({
    this.id,
    required this.patientName,
    required this.hospital,
    required this.surgeryType,
    required this.scheduledDate,
    this.status = 'scheduled',
    this.prepChecklist,
    this.intraOpNotes,
    this.postOpReport,
  });

  Map<String, dynamic> toMap() {
    return {
      if (id != null) 'id': id,
      'patient_name': patientName,
      'hospital': hospital,
      'surgery_type': surgeryType,
      'scheduled_date': scheduledDate,
      'status': status,
      'prep_checklist': prepChecklist,
      'intra_op_notes': intraOpNotes,
      'post_op_report': postOpReport,
    };
  }

  factory Surgery.fromMap(Map<String, dynamic> map) {
    return Surgery(
      id: map['id'] as int?,
      patientName: map['patient_name'] as String,
      hospital: map['hospital'] as String,
      surgeryType: map['surgery_type'] as String,
      scheduledDate: map['scheduled_date'] as String,
      status: map['status'] as String? ?? 'scheduled',
      prepChecklist: map['prep_checklist'] as String?,
      intraOpNotes: map['intra_op_notes'] as String?,
      postOpReport: map['post_op_report'] as String?,
    );
  }

  Surgery copyWith({
    int? id,
    String? patientName,
    String? hospital,
    String? surgeryType,
    String? scheduledDate,
    String? status,
    String? prepChecklist,
    String? intraOpNotes,
    String? postOpReport,
  }) {
    return Surgery(
      id: id ?? this.id,
      patientName: patientName ?? this.patientName,
      hospital: hospital ?? this.hospital,
      surgeryType: surgeryType ?? this.surgeryType,
      scheduledDate: scheduledDate ?? this.scheduledDate,
      status: status ?? this.status,
      prepChecklist: prepChecklist ?? this.prepChecklist,
      intraOpNotes: intraOpNotes ?? this.intraOpNotes,
      postOpReport: postOpReport ?? this.postOpReport,
    );
  }
}
